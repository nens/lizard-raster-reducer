from setuptools import setup

version = "0.1.dev0"

long_description = "\n\n".join([open("README.rst").read(), open("CHANGES.rst").read()])

install_requires = ["pandas", "requests", "datetime", "pyyaml"]

tests_require = [
    "pytest",
    "mock",
    "pytest-cov",
    "pytest-flakes",
    "pytest-black",
    "pyyaml",
]

setup(
    name="lizard-raster-reducer",
    version=version,
    description="Lizard raster reducer is a tool to auto-generate regional reports from Lizard data. "
    "It reduces rasters to aggregate statistics per region. "
    "Multiple rasters can be specified. The first raster will act as the scope raster. "
    "The scope raster determines the spatial extent and temporal behaviour of the result. "
    "Rasters can be temporal or static. "
    "Rasters can contain continuous values or discrete classes. "
    "Regions of one region type are used for the result. "
    "Regions within the spatial extent of the scope raster are used in the result. "
    "A configuration file is used to customize the output.",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=["Programming Language :: Python", "Framework :: Django"],
    keywords=[],
    author="Wietze Suijker",
    author_email="wietze.suijker@nelen-schuurmans.nl",
    url="https://github.com/nens/lizard-raster-reducer",
    license="MIT",
    packages=["lizard_raster_reducer"],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={"test": tests_require},
    entry_points={
        "console_scripts": [
            "run-lizard-raster-reducer = lizard_raster_reducer.scripts:main"
        ]
    },
)
