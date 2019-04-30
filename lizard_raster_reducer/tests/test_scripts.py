# -*- coding: utf-8 -*-
"""Tests for script.py"""
from lizard_raster_reducer import scripts, fetching, rasters, regions, reducer, reporter
import pickle
import yaml


LIZARD_URL = "https://demo.lizard.net/api/v3/"


def test_get_parser():
    parser = scripts.get_parser()
    # As a test, we just check one option. That's enough.
    options = parser.parse_args()
    assert options.verbose is False


def test_set_headers():
    """Notice that other tests rely on this function"""
    with open(scripts.CREDENTIALS_FILE, "r") as f:
        credentials = yaml.load(f, Loader=yaml.SafeLoader)
    username = credentials["username"]
    password = credentials["password"]
    fetching.set_headers(username, password)
    headers = fetching.get_headers()
    assert headers["username"] == username
    assert headers["password"] == password


def test_raster_collection():
    scripts.set_local_directories()
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    raster_collection = rasters.RasterCollection(
        LIZARD_URL,
        reducer_options["raster_layers"],
        reducer_options["temporal_type"],
        reducer_options["temporal_options"],
    )
    scope_raster, reducer_raster_collection, bounding_box = (
        raster_collection.fetch_raster_collection()
    )
    raster_collection = [scope_raster, reducer_raster_collection, bounding_box]
    raster_collection_file = (
        "lizard_raster_reducer/tests/testdata/test_raster_collection.pickle"
    )
    pickle.dump(raster_collection, open(raster_collection_file, "wb"))

    assert scope_raster["temporal"] is True
    assert len(reducer_raster_collection) == 2


def test_region_collection():
    scripts.set_local_directories()
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    region_type = reducer_options["region_hierarchy"][-1][0]
    bounding_box = [
        3.246545003189651,
        53.51785596141467,
        7.256670701953549,
        50.72869734511649,
    ]
    region_collection = regions.RegionCollection(
        LIZARD_URL,
        reducer_options["boundaries"],
        reducer_options["region_hierarchy"],
        region_type,
        bounding_box,
    )
    reducer_regions = region_collection.fetch_reducer_regions(True)
    reducer_regions_file = (
        "lizard_raster_reducer/tests/testdata/test_reducer_regions.pickle"
    )
    pickle.dump(reducer_regions, open(reducer_regions_file, "wb"))
    assert "area" in reducer_regions[0]


def test_reducer():
    scripts.set_local_directories()
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    region_type = reducer_options["region_hierarchy"][-1][0]
    raster_collection_file = (
        "lizard_raster_reducer/tests/testdata/test_raster_collection.pickle"
    )
    reducer_regions_file = (
        "lizard_raster_reducer/tests/testdata/test_reducer_regions.pickle"
    )
    scope_raster, reducer_raster_collection, bounding_box = fetching.unpickle(
        raster_collection_file
    )
    reducer_regions = fetching.unpickle(reducer_regions_file)
    reducer_test = reducer.Reducer(
        LIZARD_URL,
        scope_raster,
        reducer_raster_collection,
        reducer_regions,
        region_type,
        reducer_options["stats_type"],
    )
    aggregates = reducer_test.reduce2dictionary(
        reducer_options["region_hierarchy"], region_limit=5
    )
    aggregates_file = "lizard_raster_reducer/tests/testdata/test_reducer_regions.pickle"
    pickle.dump(aggregates, open(aggregates_file, "wb"))
    assert "url" in aggregates[0]


def test_reporter():
    aggregates_file = "lizard_raster_reducer/tests/testdata/test_reducer_regions.pickle"
    aggregates = fetching.unpickle(aggregates_file)
    alarms = [0.2, 0.4]
    result = reporter.export(aggregates, "test", True, True, True, alarms)
    assert result == 1


# TODO find out how to mimic user input for test function
# def test_fetch_raster():
#     raster_collection = rasters.RasterCollection(LIZARD_URL, ["Water"])
#     raster_json = raster_collection.fetch_raster("Water", False)
#     assert isinstance(raster_json, dict)


def test_unpickle():
    pickle.dump("random text", open("file.pickle", "wb"))
    file = fetching.unpickle("file.pickle")
    none = fetching.unpickle("non_existing.pickle")
    assert file == "random text"
    assert none is None
