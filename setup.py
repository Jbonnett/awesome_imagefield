from distutils.core import setup

name = 'awesome_imagefield'
setup(
    name=name,
    packages=[name, name+".form"],
    package_dir={name: name},
    package_data={
        name: [
            "static/css/*",
            "static/js/*",
            "static/image/*",
            "templates/widgets/*"
        ]},
    version="0.0.2",
    description="A awesome image field for django that supports croping",
    author="Sergio Soria, Jon Cotton, Joshua Bonnett",
    author_email="joshua.bonnett@gmail.com",
    url="http://github.com/cirlabs/awesome_imagefield",
    download_url="",
    keywords=["encoding", "i18n", "xml"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description="""\
A awesome Image Field for django that suports croping
-------------------------------------
"""
)
