lizard-raster-reducer
==========================================

Introduction
------------

Lizard raster reducer is a tool to auto-generate regional reports from Lizard data.
It "reduces" raster data to aggregate statistics for multiple regions.
Lizard API endpoints are used to retrieve data. The main ones are search, rasters, regions and raster-aggregates.
To prevent API overload, the tool creates and fills a 'lizard_cache' folder by default.

Multiple rasters can be specified. The first raster will act as the scope raster.
The scope raster determines the spatial extent and temporal behaviour of the result. Rasters can be temporal or static. Rasters can contain continuous values or discrete classes. Regions of one region type are used for the result. Regions within the spatial extent of the scope raster are used in the result. A configuration file is used to customize the output.

The results are aggregate numbers of data per region.
When the data type is interval or ratio, the average of the region is returned.
When data are classes, the area fraction per class are returned.
The output format can be specified to be CSV, JSON or HTML.


Usage
------------

1. Set options: rename options_template.yml to options.yml and specify options (template provides explanation).

2. Set credentials: rename localsecret_template.py to localsecret.py and specify Lizard credentials

3. Review optional arguments to pass: pipenv run run-lizard-raster-reducer -h

4. Run the code: pipenv run run-lizard-raster-reducer

5. Find result(s) in ./reducer_results


Installation
------------

We can be installed with::

  $ pip install lizard-raster-reducer



Development installation of this project itself
-----------------------------------------------

We're installed with `pipenv <https://docs.pipenv.org/>`_, a handy wrapper
around pip and virtualenv. Install that first with ``pip install
pipenv``. Then run::

  $ PIPENV_VENV_IN_PROJECT=1 pipenv --three
  $ pipenv install --dev

There will be a script you can run like this::

  $ pipenv run run-lizard-raster-reducer

It runs the `main()` function in `lizard-raster-reducer/scripts.py`,
adjust that if necessary. The script is configured in `setup.py` (see
`entry_points`).

In order to get nicely formatted python files without having to spend manual
work on it, run the following command periodically::

  $ pipenv run black lizard_raster_reducer

Run the tests regularly. This also checks with pyflakes, black and it reports
coverage. Pure luxury::

  $ pipenv run pytest

The tests are also run automatically `on travis-ci
<https://travis-ci.com/nens/lizard-raster-reducer>`_, you'll see it
in the pull requests. There's also `coverage reporting
<https://coveralls.io/github/nens/lizard-raster-reducer>`_ on
coveralls.io (once it has been set up).

If you need a new dependency (like `requests`), add it in `setup.py` in
`install_requires`. Afterwards, run install again to actuall install your
dependency::

  $ pipenv install --dev


Steps to do after generating with cookiecutter
----------------------------------------------

- Add a new project on https://github.com/nens/ with the same name. Set
  visibility to "public" and do not generate a license or readme.

  Note: "public" means "don't put customer data or sample data with real
  persons' addresses on github"!

- Follow the steps you then see (from "git init" to "git push origin master")
  and your code will be online.

- Go to
  https://github.com/nens/lizard-raster-reducer/settings/collaboration
  and add the teams with write access (you might have to ask someone with
  admin rights to do it).

- Update this readme. Use `.rst
  <http://www.sphinx-doc.org/en/stable/rest.html>`_ as the format.

- Ask Reinout to configure travis and coveralls.

- Remove this section as you've done it all :-)
