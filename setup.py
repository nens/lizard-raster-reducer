from setuptools import setup

version = "0.6"

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
    description="Lizard raster reducer is a tool to auto-generate regional reports from Lizard data.",
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
