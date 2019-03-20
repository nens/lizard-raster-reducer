# -*- coding: utf-8 -*-
"""TODO Docstring, used in the command line help text."""

import argparse
import os
import logging
import shutil
import sys
import yaml


from lizard_raster_reducer.rasters import RasterCollection
from lizard_raster_reducer.regions import RegionCollection
from lizard_raster_reducer.fetching import set_headers
from lizard_raster_reducer.reducer import Reducer
from lizard_raster_reducer.reporter import export

LIZARD_URL = "https://demo.lizard.net/api/v3/"
OPTIONS_FILE = "reducer_options.yml"
CREDENTIALS_FILE = "credentials.yml"
REQUESTS_HEADERS = {}
logger = logging.getLogger(__name__)


def get_parser():
    """Get parser object"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="limit the amount of regions in the output" "defaults to no limit",
    )
    # TODO add argument to use lizard cache
    return parser


def reduce_rasters(reducer_options, region_limit):
    """function that does the actual work"""
    region_type = reducer_options["region_hierarchy"][-1][0]
    raster_collection = RasterCollection(
        LIZARD_URL,
        reducer_options["raster_layers"],
        reducer_options["temporal_type"],
        reducer_options["temporal_options"],
    )
    scope_raster, reducer_raster_collection, bounding_box = (
        raster_collection.fetch_raster_collection()
    )

    region_collection = RegionCollection(
        LIZARD_URL,
        reducer_options["boundaries"],
        reducer_options["region_hierarchy"],
        region_type,
        bounding_box,
    )
    reducer_regions = region_collection.fetch_reducer_regions()
    reducer = Reducer(
        LIZARD_URL,
        scope_raster,
        reducer_raster_collection,
        reducer_regions,
        region_type,
    )

    aggregates = reducer.reduce2dictionary(
        reducer_options["region_hierarchy"], region_limit
    )

    export(
        aggregates,
        reducer_options["export_name"],
        reducer_options["export_json"],
        reducer_options["export_html"],
        reducer_options["export_csv"],
    )


def main():
    """ Call command with args from parser
        Regional report from reduced lizard rasters """
    options = get_parser().parse_args()
    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    if not options.limit:
        options.limit = None
    os.makedirs("reducer_results", exist_ok=True)
    os.makedirs("lizard_cache/colormaps", exist_ok=True)
    os.makedirs("lizard_cache/regions", exist_ok=True)
    if not os.path.exists(OPTIONS_FILE):
        template_file = os.path.join(
            os.path.dirname(__file__), "reducer_options_template.yml"
        )
        shutil.copy(template_file, OPTIONS_FILE)
        print(
            "Created a new config file in current directory: {}. Edit the config file first.".format(
                OPTIONS_FILE
            )
        )
        sys.exit(1)
    with open(OPTIONS_FILE, "r") as f:
        reducer_options = yaml.load(f)
    if not os.path.exists(CREDENTIALS_FILE):
        credentials_file = os.path.join(
            os.path.dirname(__file__), "credentials_template.yml"
        )
        shutil.copy(credentials_file, CREDENTIALS_FILE)
        print(
            "Created a new credentials file in current directory: {}. Edit the credentials file first.".format(
                CREDENTIALS_FILE
            )
        )
        sys.exit(1)
    with open(CREDENTIALS_FILE, "r") as f:
        credentials = yaml.load(f)
    username = credentials["username"]
    password = credentials["password"]

    set_headers(username, password)
    reduce_rasters(reducer_options, options.limit)


if __name__ == "__main__":
    exit(main())
