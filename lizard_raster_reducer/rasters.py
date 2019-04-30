#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create raster collection with reducer attributes"""

import logging
import pickle

from datetime import datetime as dt
from lizard_raster_reducer.fetching import (
    request_json_from_url,
    unpickle,  # select_from_list,
)

logger = logging.getLogger(__name__)


class RasterCollection:
    """
    Raster objects based on search result in Lizard from list of raster names
    Each raster name is queried in Lizard. By default this returns the first raster found.

    """

    def __init__(
        self, LIZARD_URL, raster_layers, temporal_type=None, temporal_options=None
    ):
        self.LIZARD_URL = LIZARD_URL
        self.scope_layer = raster_layers[0]
        self.raster_layers = raster_layers
        self.temporal_type = temporal_type
        self.temporal_options = temporal_options

    def fetch_raster(self, layer, first_result=True):
        """get raster json object from layer. Layer is one of raster_layers.
        A layer can point to a uuid or it can be a search query"""
        # check if a UUID is provided
        try:
            raster_url = f"{self.LIZARD_URL}rasters/{layer}/"
            raster_json = request_json_from_url(raster_url)
            return raster_json
        except:
            pass
        # check if a valid search query is provided
        search_url = f"{self.LIZARD_URL}search/"
        params = {"q": layer, "type": "rasterstore"}
        raster_search = request_json_from_url(url=search_url, params=params)
        count = raster_search["count"]
        if count == 0:
            logger.debug(
                "No raster layer found. Configure preferences in the options.yml file."
            )
        raster_search_result = raster_search["results"]
        if first_result or count == 1:
            raster_url = raster_search_result[0]["entity_url"]
        # TODO find out how to mimic user input for test function
        # else:
        #     raster_short_list = []
        #     raster_urls = [i["entity_url"] for i in raster_search_result]
        #     for raster in raster_search_result:
        #         name_url = f"{raster["title"]} (url: {raster["entity_url"]})"
        #         raster_short_list.append(name_url)
        #     help = f"Query: {layer} \nWhich item (enter_number)?"
        #     _, number = select_from_list(raster_short_list, help)
        #     raster_url = raster_urls[number]

        raster_json = request_json_from_url(raster_url)
        return raster_json

    def scope_raster_bounding_box(self, scope_raster):
        """get the spatial bounding box of the scope raster, i.e. the reducer's spatial extent"""
        spatial_bounds = scope_raster["spatial_bounds"]
        return [
            spatial_bounds["west"],
            spatial_bounds["north"],
            spatial_bounds["east"],
            spatial_bounds["south"],
        ]

    def get_raster_dates(self, raster):
        """list timesteps in 'YYYY-MM-DDTHH:MM:SS' format using temporal range of raster object.
        Timesteps are determined by the raster interval. Options.yml allows for custom interval.
        """
        if not raster["temporal"]:
            return ["1970-01-01"]
        timesteps_ms = []
        first_ms = int(raster["first_value_timestamp"])
        last_ms = int(raster["last_value_timestamp"])
        if self.temporal_type == "range":
            range_start_date = dt.combine(
                self.temporal_options["start_date"], dt.min.time()
            )
            range_end_date = dt.combine(
                self.temporal_options["end_date"], dt.min.time()
            )
            # range_end_date = self.temporal_options["end_date"]
            first_ms_in_range = int(dt.timestamp(range_start_date) * 1000)
            last_ms_in_range = int(dt.timestamp(range_end_date) * 1000)
            if first_ms_in_range > first_ms:
                first_ms = first_ms_in_range
            if last_ms_in_range <= last_ms:
                last_ms = last_ms_in_range
        if self.temporal_options["custom_interval"]:
            interval_ms = self.temporal_options["interval_days"] * 3_600_000 * 24
        else:
            interval_ms = int(raster["frequency"])
        while first_ms < last_ms:
            timesteps_ms.append(last_ms)
            last_ms -= interval_ms
        if first_ms not in timesteps_ms:
            if not self.temporal_options["custom_interval"]:
                timesteps_ms.append(first_ms)
        dates = [dt.fromtimestamp(i / 1000.0).isoformat() for i in timesteps_ms]
        return dates

    def get_gradient_colormap(self, hex_colors, styles_split, reducer_colormap):
        """return the gradient colormap definition for one raster"""
        values, colors, scaled_values = [], [], []
        for value, color in hex_colors.items():
            values.append(value)
            colors.append(color)
        if len(styles_split) == 2:
            style_min = float(styles_split[1])
            # assume highest value from data range
            style_max = max(values)
        elif len(styles_split) == 3:
            style_min, style_max = float(styles_split[1]), float(styles_split[2])
        else:
            style_min, style_max = min(values), max(values)
        scaled_values = [x * (style_max - style_min) + style_min for x in values]
        reducer_colormap["min"] = style_min
        reducer_colormap["max"] = style_max
        reducer_colormap["data"] = dict(zip(colors, scaled_values))
        return reducer_colormap

    def get_discrete_colormap(self, definition, hex_colors, reducer_colormap):
        """return the discrete colormap definition for one raster"""
        labels = next(iter(definition["labels"].values()))
        reducer_classes = []
        for label in labels:
            value, name = label
            hex_color = hex_colors[value]
            class_dict = {"label": name, "class": value, "color": hex_color}
            reducer_classes.append(class_dict)
        reducer_colormap["data"] = reducer_classes
        return reducer_colormap

    def get_reducer_colormap(self, raster, check_local=True):
        """Get gradient or discrete colormap definition based on raster configuration.
        If not set, assume gradient colormap "Blues", visualizing data from white to blue.
        For discrete colormap retrieve classes
        """
        options = raster["options"]
        if "styles" in options:
            styles = options["styles"]
        else:
            styles = "Blues:0:1"
            raster["options"] = {"styles": styles}
        styles_split = styles.split(":")
        name = styles_split[0]
        url = f"{self.LIZARD_URL}colormaps/{name}/"
        file = f"lizard_cache/colormaps/colormap_{name}.pickle"
        if check_local:
            colormap = unpickle(file)
        else:
            colormap = None
        if colormap is None:
            colormap = request_json_from_url(url)
            pickle.dump(colormap, open(file, "wb"))
        definition = colormap["definition"]
        colormap_type = definition["type"]
        data = definition["data"]
        if "invalid" in definition:
            data.insert(0, [-1, definition["invalid"]])
        hex_colors = {}
        for elem in data:
            value, rgba = elem
            r, g, b, a = rgba
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            # hex_color_alpha = f"#{r:02x}{g:02x}{b:02x}{a:02x}"
            hex_colors[value] = hex_color

        reducer_colormap = {"type": colormap_type, "name": name}
        if colormap_type == "GradientColormap":
            return self.get_gradient_colormap(
                hex_colors, styles_split, reducer_colormap
            )
        else:  # colormap_type == "DiscreteColormap":
            return self.get_discrete_colormap(definition, hex_colors, reducer_colormap)

    def get_reducer_dates(self, scope_raster):
        """get the dates for which to reduce the rasters"""
        dates = self.get_raster_dates(scope_raster)
        if self.temporal_type == "last_timesteps":
            timesteps = self.temporal_options["timesteps"]
            reducer_dates = dates[:timesteps]
        elif self.temporal_type == "range":
            start_date = self.temporal_options["start_date"].isoformat()
            end_date = self.temporal_options["end_date"].isoformat()
            reducer_dates = [date for date in dates if start_date <= date <= end_date]
        else:  # N/A, non-temporal
            reducer_dates = ["2019-01-01"]
        return reducer_dates

    def set_reducer_dates(self, scope_raster, raster_collection):
        """set the dates for which to reduce the rasters"""
        reducer_dates = self.get_reducer_dates(scope_raster)
        for raster in raster_collection:
            dates = self.get_raster_dates(raster)
            raster_reducer_dates = [
                date for date in dates if reducer_dates[-1] <= date <= reducer_dates[0]
            ]
            if raster_reducer_dates:
                raster["reducer_dates"] = raster_reducer_dates
            else:
                last_date = dt.fromtimestamp(
                    raster["last_value_timestamp"] / 1000.0
                ).isoformat()
                raster["reducer_dates"] = [last_date]
        return raster_collection

    def fetch_raster_collection(self):
        """retrieve all raster objects for the reducer tasks"""
        raster_collection = []
        for raster_layer in self.raster_layers:
            raster = self.fetch_raster(raster_layer)
            raster["colormap"] = self.get_reducer_colormap(raster)
            if raster["observation_type"] is None:
                raster["observation_type"] = {
                    "url": "",
                    "code": "",
                    "parameter": "",
                    "unit": "",
                    "scale": "",
                    "description": "",
                    "domain_values": "",
                    "reference_frame": "",
                    "compartment": "",
                }
            raster_collection.append(raster)
            if raster_layer == self.scope_layer:
                scope_raster = raster
        filtered_collection = list(filter(None.__ne__, raster_collection))
        reducer_raster_collection = self.set_reducer_dates(
            scope_raster, filtered_collection
        )
        bounding_box = self.scope_raster_bounding_box(scope_raster)
        return scope_raster, reducer_raster_collection, bounding_box
