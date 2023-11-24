from setuptools import setup, find_packages

setup(
    name="django_relay_endpoint",
    license="MIT",
    author="Gevorg Hakobyan",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type='text/markdown',

    install_requires=[
        "graphene-django>=3.1.5",
        "graphene-file-upload>=1.3.0",
        "django_filter>=23.3.0",
    ],

)
