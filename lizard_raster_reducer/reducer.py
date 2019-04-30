#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reduce and reorganize the data per region"""

import logging

from lizard_raster_reducer.fetching import parameterised_url, get_json_objects_async

logger = logging.getLogger(__name__)


class RasterAggregate:
    """Reducer formatted raster object, to be filled with aggregate data"""

    def __init__(self, hierarchy):
        self.reducer_hierarchy = {}
        for level in hierarchy:
            self.reducer_hierarchy[level[1]] = level[0]

    def get_raster_attributes(self, raster):
        """get reducer formatted raster object"""
        uuid_short = raster["uuid"].split("-")[0]
        raster_attributes = {}
        # raster_attributes = {"Raster": raster["name"]}
        data = {}
        colormap = raster["colormap"]
        if colormap["type"] == "DiscreteColormap":
            for color in colormap["data"]:
                label = color["label"]
                class_label = f"{label}_{uuid_short}"
                data[class_label] = 0
        else:  # GradientColormap
            observation_type = raster["observation_type"]
            parameter = observation_type["parameter"]
            unit = observation_type["unit"]
            raster_name = raster["name"]
            parameter_unit = f"{parameter} {unit}"
            data_label = f"{raster_name} ({parameter_unit})_{uuid_short}"
            data[data_label] = 0
        raster_attributes["data_format"] = data
        return raster_attributes

    def get_region_attributes(self, region):
        """get reducer formatted region attributes"""
        region_attributes = {"Area (ha)": region["area"]}
        if "type_nr" in region:
            for region_type_name, type_nr in self.reducer_hierarchy.items():
                if region["type_nr"] == type_nr:
                    type_name = f"Region {region_type_name}"
                    region_attributes[type_name] = region["name"]
            if "regional_context" in region:
                regional_context = region["regional_context"]
                if regional_context:
                    level = 1
                    for region_type_name, type_nr in self.reducer_hierarchy.items():
                        for context_type, context_region in regional_context.items():
                            if context_type == type_nr:
                                if len(regional_context.items()) == 1:
                                    type_name = f"Region context {region_type_name}"
                                else:
                                    type_name = (
                                        f"Region context ({level}) {region_type_name}"
                                    )
                                region_attributes[type_name] = context_region["name"]
                                level += 1
        return region_attributes

    def get_data_form(self, datetime, url, raster_attributes):
        """get reducer data form template using raster attributes"""
        metadata = {"datetime": datetime, "url": url}
        data_form = {**raster_attributes["data_format"], **metadata}
        return data_form


class Reducer:
    """
    Dataframe object based on scope raster, raster list, regions and options
    """

    def __init__(
        self,
        LIZARD_URL,
        scope_raster,
        raster_collection,
        regions,
        reducer_region_type,
        reducer_stats_type,
    ):
        self.LIZARD_URL = LIZARD_URL
        self.scope_raster = scope_raster
        self.raster_collection = raster_collection
        self.regions = regions
        self.reducer_region_type = reducer_region_type
        self.reducer_stats_type = reducer_stats_type

    def aggregation_params(self, region, raster, date):
        """get aggregation parameters from region raster and date"""
        params = {}
        params["geom_id"] = region["id"]
        params["rasters"] = raster["uuid"]
        params["styles"] = raster["options"]["styles"]
        params["srs"] = "EPSG:4326"
        raster_scale = raster["observation_type"]["scale"]
        if raster_scale in ["interval", "ratio"]:
            params["agg"] = "mean"
        else:
            params["agg"] = "counts"
        params["time"] = date
        return params

    def fetch_raster_aggregate(self, region, raster, date):
        """fetch raster aggregate for one region, raster and date"""
        params = self.aggregation_params(region, raster, date)
        url = parameterised_url(f"{self.LIZARD_URL}raster-aggregates/", params)
        return url

    def fetch_region_aggregates(self, region, raster):
        """fetch aggregates for one region, one raster, multiple dates"""
        raster_dates = raster["reducer_dates"]
        aggregate_urls = {}
        for raster_date in raster_dates:
            aggregate_urls[raster_date] = self.fetch_raster_aggregate(
                region, raster, raster_date
            )
        return aggregate_urls

    def fetch_raster_collection_aggregates(self, regions, raster_collection):
        """fetch all raster collection aggregates"""
        raster_collection_aggregates = {}
        for raster in raster_collection:
            region_aggregates = {}
            for region in regions:
                if "regional_context" not in region:
                    region["regional_context"] = {region["type_nr"]: region}
                aggregate_urls = self.fetch_region_aggregates(region, raster)
                region_aggregates[region["id"]] = {
                    "region": region,
                    "urls": aggregate_urls,
                }

            raster_collection_aggregates[raster["uuid"]] = {
                "region_aggregates": region_aggregates,
                "raster": raster,
            }
        return raster_collection_aggregates

    def get_aggregates_form(self, aggregates_raster, raster_aggregate):
        """create template to fill in aggregate data"""
        aggregates_form = []
        raster = aggregates_raster["raster"]
        raster_name = {"Raster": raster["name"]}
        raster_attributes = raster_aggregate.get_raster_attributes(raster)
        region_aggregates = aggregates_raster["region_aggregates"]
        for region_id, region_urls in region_aggregates.items():
            region = region_urls["region"]
            region_attributes = raster_aggregate.get_region_attributes(region)
            urls = region_urls["urls"]
            for datetime, url in urls.items():
                data_form = raster_aggregate.get_data_form(
                    datetime, url, raster_attributes
                )
                aggregate = {}
                aggregate_dicts = [raster_name, data_form, region_attributes]
                for d in aggregate_dicts:
                    for k, v in d.items():
                        aggregate.setdefault(k, v)
                aggregates_form.append(aggregate)
        return aggregates_form

    def fill_aggregates_form(self, aggregates_form, raster_aggregates):
        """fill data template with data"""
        for raster_aggregate in raster_aggregates:
            for url, json_dict in raster_aggregate.items():
                data = json_dict["data"]
                if isinstance(data, list):
                    counts_data = True
                    if None in data:
                        data = 0
                        counts_data = False
                else:
                    counts_data = False
                for aggregate in aggregates_form:
                    if url == aggregate["url"]:
                        uuid_short = (
                            url.partition("rasters=")[2].split("&")[0].split("-")[0]
                        )
                        if "counts" in url and counts_data:
                            for elem in data:
                                if "label" in elem:
                                    elem_label = elem["label"]
                                    label = f"{elem_label}_{uuid_short}"
                                    portion = round(elem["data"] / elem["total"], 3)
                                    area = round(aggregate["Area (ha)"] * portion, 1)
                                else:
                                    elem["label"] = ""
                                    label = uuid_short
                                    portion = 0
                                    area = 0
                                if self.reducer_stats_type == "areas":
                                    aggregate[label] = area
                                else:
                                    aggregate[label] = portion
                        else:  # mean
                            aggregate_data = {}
                            for k, v in aggregate.items():
                                if uuid_short in k.lower():
                                    aggregate_data[k] = data
                            aggregate.update(aggregate_data)
        aggregates = aggregates_form
        return aggregates

    def reduce2dictionary(self, hierarchy, region_limit=False):
        """convert aggregates to dictionary"""
        if region_limit:
            # reduce only the region_limit amount of regions
            self.regions = self.regions[0:region_limit]

        raster_aggregate = RasterAggregate(hierarchy)
        raster_collection_aggregates = self.fetch_raster_collection_aggregates(
            self.regions, self.raster_collection
        )
        reducer_aggregates = []
        for raster_uuid, aggregates_raster in raster_collection_aggregates.items():
            aggregates_form = self.get_aggregates_form(
                aggregates_raster, raster_aggregate
            )
            reducer_aggregates.extend(aggregates_form)
        aggregate_urls = [elem["url"] for elem in reducer_aggregates]

        raster_aggregates = get_json_objects_async(aggregate_urls)

        aggregates = self.fill_aggregates_form(reducer_aggregates, raster_aggregates)
        return aggregates
