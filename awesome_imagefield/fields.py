import os.path
from PIL import Image
import StringIO

from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import ImageFileDescriptor

from south.modelsinspector import add_introspection_rules
from .form.fields import VersionedImageField as CropperFormField


# South migrations support for custom fields
add_introspection_rules([], ["^awesome_imagefield\.fields\.VersionedImageField"])
add_introspection_rules([], ["^awesome_imagefield\.fields\.SquareAutoCropVersionedImageField"])


class ImageVersionSet(object):

    def __init__(self, field, model_instance, filename):
        self.field = field
        self.filename = filename
        self.model_instance = model_instance

        '''
        To get a set of ALL image versions which can be accessed from
        templates, append the collection of `autosize_versions` from models to
        existing image versions.
        '''
        # Copy existing versions, find their 'autosize_versions' (if any), and
        # copy those to the top level of versions. To avoid recursion
        # problems, start with an empty dict and copy elements in.
        flat_versions = {}
        for version, attribs in field.versions.items():
            if 'autosize_versions' in attribs:
                flat_versions.update(attribs['autosize_versions'])
            flat_versions[version] = attribs

        self._versions = flat_versions

    def __getattr__(self, name):

        try:
            filepath = self._versions[name]['upload_to'](self.model_instance, self.filename)

        except (AttributeError, LookupError):
            return None

        if filepath and self.field.storage.exists(filepath):
            field_file_object = self.field.attr_class(self.model_instance, self.field, filepath)
        else:
            return None

        return field_file_object


class VersionedImageFileDescriptor(ImageFileDescriptor):

    def __get__(self, instance=None, owner=None):
        val = super(VersionedImageFileDescriptor, self).__get__(instance, owner)
        if not getattr(val, 'versions', None):
            setattr(val, 'versions', ImageVersionSet(self.field, instance, val.name))
        return val


class BaseVersionedImageField(models.ImageField):
    descriptor_class = VersionedImageFileDescriptor

    def __init__(self, versions=None, upload_to='', use_field_name_as_file_name=False, *args, **kwargs):
        self.versions = versions
        self.use_field_name_as_file_name = use_field_name_as_file_name

        # In order to use the field name as the file name, we need to change how `upload_to` is used
        # We save it for use later in our custom generate_filename(); do not pass into parent constructor
        if use_field_name_as_file_name and callable(upload_to):
            self._upload_to = upload_to

            #KLUDGE Django Model Validation requires FileFields to provide a non-empty `upload_to`
            # we give it True to pass validation, but it's not callable() so it won't be used
            # http://bit.ly/NVN1NF
            return super(BaseVersionedImageField, self).__init__(upload_to=True, *args, **kwargs)

        return super(BaseVersionedImageField, self).__init__(upload_to=upload_to, *args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Skip parent pre_save()s because we want to delete the file before save()
        and save() doesn't override existing files

        Note:
        1. This will not delete files off the disk when the file value is cleared.
           This is standard Django behavior.

        2. This will not delete prior files that have a different extension.
           eg: Replacing a JPG file by uploading a PNG will result in a second
               set of files: 'profile_pic.original.jpg' and 'profile_pic.original.png'
        """
        # Normally happens in django.db.models.fields.__init__.pr->Field.pre_save()
        file = getattr(model_instance, self.attname)
        if file and not file._committed:  # normally happens in django.db.models.fields.files.py->FileField.pre_save()
            # filename is created in FieldFile.save() so we need to replicate what it will be
            on_disk_filename = self.generate_filename(model_instance, file.name)

            # now delete the file that we expect to save
            self.storage.delete(on_disk_filename)

            # Commit the file to storage prior to saving the model.
            # Normally happens in django.db.models.fields.files.py->FileField.pre_save()
            file.save(file.name, file, save=False)
        return file

    def get_filename(self, filename):
        # Set the name of the Field as the filename but keep original extension
        custom_name = "%s%s" % (self.name, os.path.splitext(filename)[1]) if self.use_field_name_as_file_name else None
        return os.path.normpath(self.storage.get_valid_name(custom_name or filename))

    def generate_filename(self, instance, filename):
        """Use upload_to() if provided. This follows Django's normal paradigm."""

        custom_name = self.get_filename(filename)
        if hasattr(self, '_upload_to'):
            return self._upload_to(instance, custom_name)
        return super(BaseVersionedImageField, self).generate_filename(instance, custom_name)

    def gen_auto_crop_version(self, version, img):
        #returns the bounding box in the form of (x,y,x1,y1) where x and y are the
        # upper left and x1 and y1 are the lower right.
        aspect = version['width'] / float(version['height'])
        # for 4/3 aspect is 1.33333 etc
        width = img.size[0]
        height = img.size[1]
        # if the image is taller than we need for this width
        if (width / aspect <= height):
            crop_width = width
            crop_height = width / aspect
            offset = (0, (height - crop_height)/2)
        # the image is too short
        elif(height * aspect < width):
            crop_height = height
            crop_width = height * aspect
            offset = ((width - crop_width)/2, 0)
        else:
            raise Exception("you should never be here, the image is probably too small")
        out = dict(
            x=int(offset[0]),
            y=int(offset[1]),
            x2=int(crop_width + offset[0]),
            y2=int(crop_height + offset[1]),
        )
        return out

    def _file_save(self, new_pil_obj, version, format, model_instance, file):
        """Save our version files to disk"""

        img_version_buffer = StringIO.StringIO()
        new_pil_obj.save(img_version_buffer, format)

        img_version_buffer = InMemoryUploadedFile(
            file=img_version_buffer,
            field_name=None,
            name='foo',
            content_type='image/%s' % format,
            size=img_version_buffer.len,
            charset=None)
        img_version_buffer.open()  # reopen just in case, which sets Django's File-like object to seek=0

        filename = version['upload_to'](model_instance, file.name)

        # delete first to prevent save() from possibily creating a new uniquely named file
        # we want to replace the file, which save() may not do natively
        file.field.storage.delete(filename)
        file.field.storage.save(filename, img_version_buffer)


class VersionedImageField(BaseVersionedImageField):

    def __init__(self, autosave_overwrite=False, *args, **kwargs):
        self.autosave_overwrite = autosave_overwrite

        super(VersionedImageField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        """Change the default Form Field this Model Field uses"""

        defaults = {'form_class': CropperFormField}
        defaults.update(kwargs)
        return super(VersionedImageField, self).formfield(**defaults)

    def pre_save(self, model_instance, add):
        """Create our image versions given transform data provided by the Form Field"""

        file = super(VersionedImageField, self).pre_save(model_instance, add)
        if file:
            try:
                img_pil_org = Image.open(file)
            except:
                file.open()  # reopen which sets Django's File-like object to seek=0
                img_pil_org = Image.open(file)

            if not hasattr(file, 'version_transform_data'):
                # check if a image version already exists
                vt_data = dict()
                for version_id, version_data in file.field.versions.items():
                    # does a version allready exist?
                    # If so dont create a automatic one for no reason
                    filename = version_data['upload_to'](model_instance, file.name)
                    # import pdb; pdb.set_trace()
                    # OK to overwrite image of the same name if `overwrite` flag was passed
                    if (file.field.autosave_overwrite) or (not file.field.storage.exists(filename)):
                        vt_data[version_id] = self.gen_auto_crop_version(version_data, img_pil_org)
                file.version_transform_data = vt_data

            # Loop through image versions present on BCImage edit page or auto
            # those which have been auto created
            for version_id, version_data in file.version_transform_data.items():

                version = file.field.versions[version_id]
                crop = img_pil_org.crop((version_data['x'], version_data['y'], version_data['x2'], version_data['y2']))
                if version['width'] != (version_data['x2'] - version_data['x']):
                    crop = crop.resize((version['width'], version['height']), Image.ANTIALIAS)
                self._file_save(crop, version, img_pil_org.format, model_instance, file)

                # Manually cropped version is now saved; now auto-save resized variants of it.
                # File object just saved is "crop" - rename to avoid confusion (we're done cropping).
                newimg = crop

                # Save multiple resized versions of the cropped image
                if 'autosize_versions' in version:
                    for version, attribs in version['autosize_versions'].items():
                        newimg = newimg.resize((attribs['width'], attribs['height']), Image.ANTIALIAS)
                        self._file_save(newimg, attribs, img_pil_org.format, model_instance, file)

            delattr(file, 'version_transform_data')
        return file


class SquareAutoCropVersionedImageField(BaseVersionedImageField):
    def pre_save(self, model_instance, add):
        """Create our autocropped image versions"""

        file = super(SquareAutoCropVersionedImageField, self).pre_save(model_instance, add)
        # _file will be None except on new uploads
        if file and (getattr(file, '_file') or hasattr(model_instance, '_porting_images_flag')):
            fp = file._file
            # HACK TODO for profile image porting; remove after launch
            if getattr(model_instance, '_porting_images_flag', False):
                fp = getattr(model_instance, self.attname)

            fp.open()  # reopen just in case, which sets Django's File-like object to seek=0
            img_pil_org = Image.open(fp)

            # Crop: find largest square that fits in the image
            org_w, org_h = img_pil_org.size
            minsize = min(org_w, org_h)  # get the smaller dimension
            w_offset = int((org_w - minsize) / 2)
            h_offset = int((org_h - minsize) / 2)
            square = img_pil_org.crop((w_offset, h_offset, w_offset + minsize, h_offset + minsize))

            # Resize: create all the different file versions
            for _, version in self.versions.items():
                # width both times just to be certain
                new = square.resize((version['width'], version['width']), Image.ANTIALIAS)
                self._file_save(new, version, img_pil_org.format, model_instance, file)
        return file
