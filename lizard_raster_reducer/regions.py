#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Retrieve regions and region attributes for reducer"""

import pickle
import logging

from lizard_raster_reducer.fetching import (
    flatten,
    request_json_from_url,
    get_json_objects_async,
    unpickle,
)

logger = logging.getLogger(__name__)


class RegionCollection:
    """
    Region objects from:
    - bounding box scope layer
    - region types in hierarchy
    """

    def __init__(self, LIZARD_URL, boundaries, hierarchy, region_type, bounding_box):
        self.LIZARD_URL = LIZARD_URL
        self.boundaries = boundaries
        self.hierarchy = hierarchy
        self.reducer_region_type = region_type
        self.bounding_box = ",".join(str(i) for i in bounding_box)
        self.bounding_box_rough = "_".join(str(round(i)) for i in bounding_box)

    def get_paginated_features(self, json_response, page_size=10):
        """return all regions, using the paginated api results
        regions are requested from paginated features, 10 per page"""
        features = json_response["results"]["features"]
        count = json_response["count"]
        next_page = json_response["next"]
        nr_of_pages = int(count / page_size) + (count % page_size > 0)
        if nr_of_pages > 1:
            page_numbers = list(range(2, nr_of_pages + 1))
            next_pages = [
                next_page.replace("page=2", f"page={n}") for n in page_numbers
            ]
            responses = get_json_objects_async(next_pages)
            for response in responses:
                for url, json_object in response.items():
                    features.extend(json_object["results"]["features"])
        return features

    def fetch_regions(self, check_local=True):
        """fetch regions. When locally available load from pickle file, else fetch from urls"""
        regions = []
        url = f"{self.LIZARD_URL}regions/"
        hierarchy = self.hierarchy
        type_numbers, type_names = map(list, zip(*hierarchy))
        params = {"in_bbox": self.bounding_box}
        for type_number in type_numbers:
            regions_file = f"lizard_cache/regions/regions_{type_number}_{self.bounding_box_rough}.pickle"
            if check_local:
                features = unpickle(regions_file)
            else:
                features = None
            if features is None:
                params["type"] = type_number
                json_response = request_json_from_url(url, params)
                features = self.get_paginated_features(json_response)
                pickle.dump(features, open(regions_file, "wb"))
            regions.append([type_number, features])
        return regions

    def get_regional_context(self, raw_regions, boundaries, hierarchy):
        """return regional context for all reducer regions"""
        regional_context = {}
        for region_type in raw_regions:
            type_number, features = region_type
            type_regions = []
            for region in features:
                region_in_context = RegionContext(region, boundaries, hierarchy)
                type_regions.append(vars(region_in_context))
            regional_context[type_number] = type_regions
        return regional_context

    def nearest_regions(self, input_region, regions):
        """sort context regions based on proximity to centroid of input region"""
        centroid = input_region["centroid"]
        context_types = input_region["context_types"]
        regional_context = {}
        if context_types is None:
            return regional_context
        for type_number in context_types:
            proximity_of_regions = []
            type_regions = regions[type_number]
            for region in type_regions:
                diff = abs(centroid[0] - region["centroid"][0]) + abs(
                    centroid[1] - region["centroid"][1]
                )
                proximity_of_regions.append([diff, region])
            nearest_regions = [
                i[1] for i in sorted(proximity_of_regions, key=(lambda x: x[0]))
            ]
            regional_context[type_number] = nearest_regions[0]
        return regional_context

    def fetch_reducer_regions(self, check_local):
        """get region objects that will be used to reduce rasters"""
        raw_regions = self.fetch_regions(check_local)
        regional_context = self.get_regional_context(
            raw_regions, self.boundaries, self.hierarchy
        )
        reducer_regions = regional_context[self.reducer_region_type]
        for reducer_region in reducer_regions:
            reducer_region["regional_context"] = self.nearest_regions(
                reducer_region, regional_context
            )
        return reducer_regions


class RegionContext:
    """the regions that form the context of a region,
    e.g. the province that a municipality is part of"""

    def __init__(self, region, boundaries, hierarchy):
        self.id = region["id"]
        self.name = region["properties"]["name"]
        self.area = region["properties"]["area"] / 10000
        self.type_name = region["properties"]["type"]
        self.type_nr = list(boundaries.keys())[
            list(boundaries.values()).index(self.type_name)
        ]
        self.context_types = self.hierarchy_context(hierarchy)
        xmin, ymax, xmax, ymin = self.region_bbox(region)
        self.bounding_box = ",".join(str(i) for i in [xmin, ymax, xmax, ymin])
        self.centroid = [(xmin + xmax) / 2, (ymin + ymax) / 2]

    def region_bbox(self, region):
        """get region bounding box from lizard region json object"""
        geometry = region["geometry"]
        geometry_coordinates = geometry["coordinates"]
        flat_coordinates = flatten(geometry_coordinates)
        coordinates = [
            flat_coordinates[i : i + 3] for i in range(0, len(flat_coordinates), 3)
        ]
        x_coordinates = [coordinate[0] for coordinate in coordinates]
        y_coordinates = [coordinate[1] for coordinate in coordinates]
        xmin = min(x_coordinates)
        ymax = max(y_coordinates)
        xmax = max(x_coordinates)
        ymin = min(y_coordinates)
        return xmin, ymax, xmax, ymin

    def hierarchy_context(self, hierarchy):
        """"get lizard type numbers to translate hierarchy options to lizard boundaries"""
        type_numbers, type_names = [], []
        for level in hierarchy:
            type_numbers.append(level[0])
            type_names.append(level[1])
        region_context_numbers = type_numbers[: type_numbers.index(self.type_nr)]
        if region_context_numbers:
            return region_context_numbers
        else:
            return None
