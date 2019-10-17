# -*- coding: utf-8 -*-
"""Scripts to reduce raster data to regional aggregates, set alarms and export as reports"""

import argparse
import json
import os
import logging
import shutil
import subprocess
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
        "-c",
        "--cache",
        action="store_true",
        default=True,
        help="store lizard data in local cache",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=None,
        help="limit the amount of regions in the output. Defaults to no limit",
    )
    return parser


def set_local_directories():
    """dirs for results and cache"""
    os.makedirs("reducer_results", exist_ok=True)
    os.makedirs("lizard_cache/colormaps", exist_ok=True)
    os.makedirs("lizard_cache/regions", exist_ok=True)


def set_local_config_files():
    """load config from yaml files"""
    config_files_set = True
    if not os.path.exists(OPTIONS_FILE):
        template_file = os.path.join(
            os.path.dirname(__file__), "reducer_options_template.yml"
        )
        shutil.copy(template_file, OPTIONS_FILE)
        print(
            f"Created a new config file in current directory: {OPTIONS_FILE}. Edit the config file first."
        )
        config_files_set = False

    if not os.path.exists(CREDENTIALS_FILE):
        credentials_file = os.path.join(
            os.path.dirname(__file__), "credentials_template.yml"
        )
        shutil.copy(credentials_file, CREDENTIALS_FILE)
        print(
            f"Created a new credentials file in current directory: {CREDENTIALS_FILE}. "
            f"Edit the credentials file first."
        )
        config_files_set = False

    if not config_files_set:
        sys.exit(1)


def raster_reducer(reducer_options, cache, region_limit):
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
    if reducer_options["custom_bounding_box"]:
        bbox = reducer_options["bounding_box"]
        bounding_box = [bbox["west"], bbox["north"], bbox["east"], bbox["south"]]
    region_collection = RegionCollection(
        LIZARD_URL,
        reducer_options["boundaries"],
        reducer_options["region_hierarchy"],
        region_type,
        bounding_box,
    )
    reducer_regions = region_collection.fetch_reducer_regions(cache)
    reducer = Reducer(
        LIZARD_URL,
        scope_raster,
        reducer_raster_collection,
        reducer_regions,
        region_type,
        reducer_options["stats_type"],
    )

    aggregates = reducer.reduce2dictionary(
        reducer_options["region_hierarchy"], region_limit
    )
    if reducer_options["alarms"]:
        raster_le = reducer_options["raster_less_equal"]
        raster_ge = reducer_options["raster_greater_equal"]
        alarms = [raster_le, raster_ge]
    else:
        alarms = None

    export(
        aggregates,
        reducer_options["export_name"],
        reducer_options["export_json"],
        reducer_options["export_html"],
        reducer_options["export_csv"],
        alarms,
    )


def replace_file_line(file, pattern, new_line):
    with open(file, "r") as f:
        lines = f.readlines()
    with open(file, "w") as f:
        for line in lines:
            if pattern in line:
                f.write(new_line)
            else:
                f.write(line)


def reducer_results_to_pivot_table(name):
    # rename src table data file
    src = "react_pivot_table/src/"
    table_js_file = f"{src}components/Table.js"
    table_js_new_line = f"""import dataframe from '../../../reducer_results/smartseeds_{name}.json';\n"""
    replace_file_line(table_js_file, ".json", table_js_new_line)
    # configure index for pivot table preset
    data_file = f"reducer_results/smartseeds_{name}.json"
    data = json.load(open(data_file))
    rows = list(data[0].keys())
    # rows.remove("Raster")
    # rows.remove("Date")
    # rows.remove("url")
    # rows.remove("Area ha")
    # rows.remove("Sub-district")
    # rows.remove("District")
    # rows.remove("Province")
    # rows.insert(0, rows.pop(rows.index("Area ha")))
    # rows.insert(0, rows.pop(rows.index("Village")))
    # rows.insert(8, rows.pop(rows.index("Sub-district")))
    # rows.insert(9, rows.pop(rows.index("District")))
    # rows.insert(10, rows.pop(rows.index("Province")))
    index_js_src_file = f"{src}index.js"

    if "Date" not in data[0]:
        # TODO better presets / more options
        vals = rows[0]
        # rows.remove(rows[1])
        renderer = "Table"
        index_js_src_line = (
                """ReactDOM.render(<TableC hiddenFromAggregators={["%s"]} hiddenFromDragDrop={["%s"]} """
                """rendererName={"%s"} aggregatorName={["Sum"]} rows={%s} vals={["%s"]} """
                """unusedOrientationCutoff={Infinity} />, wrapper);""" % (rows, rows, renderer, rows, vals)
        )
    else:
        vals = rows[0]
        renderer = "Line Chart"
        # renderer = "Grouped Column Chart"
        index_js_src_line = (
                # """ReactDOM.render(<TableC rendererName={"%s"} """
                # """aggregatorName={["Sum"]} rows={["Province"]} cols={["Date"]} vals={["%s"]} """
                # """unusedOrientationCutoff={Infinity} />, wrapper);""" % (renderer, vals)
        # TODO deal with list variables (e.g. rows, vals in text!!
                """ReactDOM.render(<TableC hiddenFromAggregators={"%s"} hiddenFromDragDrop={"%s"} rendererName={"%s"} """
                """aggregatorName={["Average"]} rows={["Province"]} cols={["Date"]} vals={["%s"]} """
                """unusedOrientationCutoff={Infinity} />, wrapper);""" % (rows, rows, renderer, vals)
                # """unusedOrientationCutoff={Infinity} />, wrapper);""" % (rows, rows, renderer, rows, vals)
        )

    replace_file_line(index_js_src_file, "ReactDOM.render", index_js_src_line)

    # create pivot table
    subprocess.call("npm run build", shell=True, cwd="react_pivot_table")
    # rename dist index and js reference
    dist = "react_pivot_table/dist/"
    index_html_file = f"{dist}index.html"
    file_name = name.replace(" ", "_")
    main_js_name = f"main_{file_name}.js"
    index_main_js_line = f"""<script type="text/javascript" src="{main_js_name}"></script></body>"""
    replace_file_line(index_html_file, """src="main""", index_main_js_line)
    table_title = f"    <title>{name}</title>"
    replace_file_line(index_html_file, "</title>", table_title)
    # copy and rename dist files
    shutil.copyfile(f"{dist}index.html", f"{dist}smartseeds/{file_name}.html")
    shutil.copyfile(f"{dist}main.js", f"{dist}smartseeds/{main_js_name}")

def main():
    """ Call command with args from parser
        Regional report from reduced lizard rasters """
    options = get_parser().parse_args()
    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    set_local_directories()
    set_local_config_files()
    with open(OPTIONS_FILE, "r") as f:
        reducer_options = yaml.load(f, Loader=yaml.SafeLoader)
    with open(CREDENTIALS_FILE, "r") as f:
        credentials = yaml.load(f, Loader=yaml.SafeLoader)
    username = credentials["username"]
    password = credentials["password"]
    set_headers(username, password)
    # raster_reducer(reducer_options, options.cache, options.limit)
    with open("smartseeds_name_uuid.csv") as f:
        smartseeds_data_sets = f.read().splitlines()
        for smartseeds_data_set in smartseeds_data_sets:
            name, uuid = smartseeds_data_set.split(";")
            reducer_options["raster_layers"] = [uuid]
            reducer_options["export_name"] = f"smartseeds_{name}"
            raster_reducer(reducer_options, options.cache, options.limit)
            reducer_results_to_pivot_table(name)



if __name__ == "__main__":
    exit(main())
