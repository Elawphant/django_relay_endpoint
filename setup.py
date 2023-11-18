from setuptools import setup

setup(
    name="django_graphene_endpoint",
    license="MIT",
    author="Gevorg Hakobyan",

    install_requires=[
        "graphene-django>=3.1.5",
        "graphene-file-upload>=1.3.0",
        "django_filter>=23.3.0",
    ],

)
