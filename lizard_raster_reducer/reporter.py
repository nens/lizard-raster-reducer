# -*- coding: utf-8 -*-
"""reporter to export aggregates to a file"""
import json
import pandas as pd

pd.set_option("display.max_colwidth", -1)


def slim_aggregates(aggregates):
    slimmed_aggregates = []
    for aggregate in aggregates:
        verbose_keys = list(aggregate.keys())
        for verbose_key in verbose_keys:
            slim_key = verbose_key.split("_")[0]
            aggregate[slim_key] = aggregate.pop(verbose_key)
        datetime = aggregate["datetime"]
        aggregate["date"] = datetime.split("T")[0] + "Z"
        aggregate.pop("datetime", None)
        slimmed_aggregates.append(aggregate)
    return slimmed_aggregates


def export(aggregates, file, export_json, export_html, export_csv, slim=True):
    """function to export aggregate data to disk in json, html or csv format"""
    if slim:
        aggregates = slim_aggregates(aggregates)
    folder = "reducer_results/"
    if export_json:
        json_file = f"{folder}{file}.json"
        with open(json_file, "w") as f:
            json.dump(aggregates, f)
    df = pd.DataFrame(aggregates)
    if export_html:
        html_name = f"{folder}{file}.html"
        df.to_html(html_name)
    if export_csv:
        csv_name = f"{folder}{file}.csv"
        df.to_csv(csv_name)
    return 1
