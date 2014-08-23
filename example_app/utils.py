from datetime import datetime
from os import path


def image_path(base_dir="images"):
    def get_image_path(instance, filename):
        return "uploaded/%s/%s/%s/%s/original/%s" % (
            base_dir,
            datetime.now().year,
            datetime.now().month,
            instance.slug,
            filename
        )
    return get_image_path


# returns a version path function that is
# prepopulated with the image version
def get_version_path(version, base_dir="images"):
    def func(instance, filename):
        org_path, org_filename = path.split(filename)
        org_path = org_path.split('/')
        return 'uploaded/%s/%s/%s/%s/%s/%s' % (
            base_dir,
            org_path[2],
            org_path[3],
            org_path[4],
            version,
            org_filename
        )
    return func


def get_generic_path(instance, filename):
    return u"uploaded/images/generic/%s/%s/%s/%s" % \
    (
        datetime.now().year,
        datetime.now().month,
        instance.slug,
        filename
    )


def image_version_filename(new_version, string, original_version='original'):
    return new_version.join(string.split(original_version))
