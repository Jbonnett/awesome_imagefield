from django import forms
from .widgets import VersionedImageCropperInput


class VersionedImageField(forms.ImageField):
    widget = VersionedImageCropperInput

    def clean(self, data, initial=None):
        """
        Receives output from VersionedImageCropperInput Widget
        where `data` is expected to be (original, versions) but
        it can also handle output from a normal File Widget. In
        the second case, the file will not have crop data and the
        versions will not be created so the field will essentially
        be incomplete.

        """
        try:  # VersionedImageCropperInput widget output
            image_file = data[0]
            crop_data = data[1]
        except (KeyError, TypeError):  # standard File widget output
            image_file = data
            crop_data = {}

        original = super(VersionedImageField, self).clean(image_file, initial)
        vtd = {}
        for version_id, version_data in crop_data.items():
            vtd[version_id] = {}
            for coord in ['x', 'y', 'x2', 'y2']:
                if version_data[coord]:
                    try:
                        vtd[version_id][coord] = int(float(version_data[coord]))
                    except (OverflowError, ValueError):
                        #Throw ValidationError instead
                        del vtd[version_id]
                        break
                else:
                    #Throw ValidationError instead
                    del vtd[version_id]
                    break
                #Check data - throw validationerror if !(x > x2) or !(y > y2)
                #maybe test and make sure the coords are within the image range
        if original and vtd:
            original.version_transform_data = vtd
        return original
