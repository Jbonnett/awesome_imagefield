from django.contrib import admin
from django import forms

from awesome_imagefield.fields import VersionedImageField
from awesome_imagefield.forms.widgets import VersionedImageCropperInput
from .models import ExampleImage


class ImageAdmin(admin.ModelAdmin):

    formfield_overrides = {
        VersionedImageField: {'widget': VersionedImageCropperInput},
    }
    list_display = ('admin_image', 'title')
    list_display_links = ('admin_image', 'title')


admin.site.register(ExampleImage, ImageAdmin)
