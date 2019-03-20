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
        credentials = yaml.load(f)
    username = credentials["username"]
    password = credentials["password"]
    fetching.set_headers(username, password)
    headers = fetching.get_headers()
    assert headers["username"] == username
    assert headers["password"] == password


def test_raster_collection():
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile)
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

    assert scope_raster["name"] == "AHN2 WSS"
    assert len(reducer_raster_collection) == 2


def test_region_collection():
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile)
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
    reducer_regions = region_collection.fetch_reducer_regions()
    reducer_regions_file = (
        "lizard_raster_reducer/tests/testdata/test_reducer_regions.pickle"
    )
    pickle.dump(reducer_regions, open(reducer_regions_file, "wb"))
    assert "area" in reducer_regions[0]


def test_reducer():
    with open("lizard_raster_reducer/tests/test_reducer_options.yml", "r") as ymlfile:
        reducer_options = yaml.load(ymlfile)
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
    result = reporter.export(aggregates, "test", True, True, True)
    assert result == 1
