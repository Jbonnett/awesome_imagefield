import simplejson as json

from django.conf import settings
from django.forms.widgets import ClearableFileInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class VersionedImageCropperInput(ClearableFileInput):
    """
    These values correspond to the coordinate names expected by JCrop
    """
    fields = ['x', 'y', 'x2', 'y2']

    class Media:
        css = {"all": ("css/jquery.Jcrop.min.css", "css/jquery.Jcrop.tbc.min.css")}
        js = ("js/jquery.Jcrop.min.js", "js/imageversion.js")

    def render(self, name, value, attrs=None):
        file_browser = super(VersionedImageCropperInput, self).render(name, value, attrs)
        crop_fields = ""
        if value and hasattr(value, 'field'):
            for version_id, version in value.field.versions.items():
                cropfield_map = dict(map(lambda x: (x, self.getFieldName(name, version_id, x)), self.fields))
                version_params = {
                    'name': self.getFieldPrefixVersioned(name, version_id),
                    'label': version['label'],
                    'original': value,
                    'version': getattr(value.versions, version_id),
                    'hidden_inputs': cropfield_map.values(),
                    'cropfield_map': json.dumps(cropfield_map),
                    'width': version['width'],
                    'height': version['height']
                }
                crop_fields += render_to_string('widgets/imageversion.html', version_params)

        return mark_safe(file_browser + crop_fields)

    def value_from_datadict(self, data, files, db_field_name):
        versions = {}
        for form_field_name, form_field_value in data.items():
            if self.isImageversionField(db_field_name, form_field_name):
                coord, version_id = self.splitFieldName(db_field_name, form_field_name)
                versions.setdefault(version_id, {})[coord] = form_field_value

        original = super(VersionedImageCropperInput, self).value_from_datadict(data, files, db_field_name)
        return (original, versions)

    """
    Utility functions for building/parsing the form field's 'name'
    """
    def isImageversionField(self, db_field_name, form_field_name):
        return form_field_name.startswith(self.getFieldPrefix(db_field_name))

    def getFieldPrefix(self, name):
        return "imageversion_%s" % name

    def getFieldPrefixVersioned(self, name, version_id):
        return '%s_%s' % (self.getFieldPrefix(name), version_id)

    def getFieldName(self, name, version_id, coord):
        return '%s_%s' % (self.getFieldPrefixVersioned(name, version_id), coord)

    def splitFieldName(self, db_field_name, form_field_name):
        prefix = self.getFieldPrefix(db_field_name)
        field_suffix = form_field_name[len(prefix) + 1:]
        split_point = field_suffix.rfind('_')
        return field_suffix[split_point+1:], field_suffix[:split_point]
