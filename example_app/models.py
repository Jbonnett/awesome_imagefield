from django.db import models
from django.utils.datastructures import SortedDict

from .utils import get_generic_path, get_version_path, image_path
from awesome_imagefield.fields import VersionedImageField


# Dictionaries of autosize properties are referenced as 'autosize_versions'
# from main image sizes dict. If new groupings are created in the future, they
# must have the same aspect ratios as manual crop settings (i.e. same as the
# `image_versions` dict below).
autosize_dimensions_3_2 = SortedDict([
    ('large_3_2', {'label': 'Large 4:3', 'width': 800, 'height': 533, 'upload_to': get_version_path('large_3_2')}),
    ('med_3_2', {'label': 'Medium 4:3', 'width': 400, 'height': 267, 'upload_to': get_version_path('med_3_2')}),
    ('small_3_2', {'label': 'Small 4:3', 'width': 180, 'height': 120, 'upload_to': get_version_path('small_3_2')}),
])

autosize_dimensions_16_9 = SortedDict([
    ('large_16_9', {'label': 'Large 16:9', 'width': 800, 'height': 450, 'upload_to': get_version_path('large_16_9')}),
    ('med_16_9', {'label': 'Medium 16:9', 'width': 400, 'height': 225, 'upload_to': get_version_path('med_16_9')}),
    ('small_16_9', {'label': 'Small 16:9', 'width': 180, 'height': 100, 'upload_to': get_version_path('small_16_9')}),
])

# These versions will appear as crop options in the admin
image_versions = SortedDict([
    ('max_16_9', {'label': 'Lead art 16:9', 'width': 1200, 'height': 675, 'upload_to': get_version_path('max_16_9'), 'autosize_versions': autosize_dimensions_16_9}),
    ('max_3_2', {'label': 'Lead art 3:2', 'width': 1200, 'height': 800, 'upload_to': get_version_path('max_3_2'), 'autosize_versions': autosize_dimensions_3_2}),
])


class ExampleImage(models.Model):
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    file = VersionedImageField(
        upload_to=image_path(),
        versions=image_versions,
        verbose_name="Image",
        max_length=255,
    )

    objects = models.Manager()

    def save(self, *args, **kwargs):
        self.width = self.file.width
        self.height = self.file.height
        return super(self, ExampleImage).save(self, *args, **kwargs)

    def get_absolute_url(self):
        return u"%s" % self.file.url

    def admin_image(self):
        """
        unfortunate hack to get images to show up in the admin. 
        There is probably a better way to do this.
        """
        try:
            return '<img src="%s"/>' % self.file.versions.small_3_2.url
        except:
            return 'broken image'
    admin_image.allow_tags = True


