# -*- coding: utf-8 -*-
"""reporter to export aggregates to a file"""
import json
import pandas as pd

pd.set_option("display.max_colwidth", -1)


def export(aggregates, file, export_json, export_html, export_csv):
    """function to export aggregate data to disk in json, html or csv format"""
    folder = "reducer_results/"
    if export_json:
        json_file = "{}{}.json".format(folder, file)
        with open(json_file, "w") as f:
            json.dump(aggregates, f)
    df = pd.DataFrame(aggregates)
    if export_html:
        html_name = "{}{}.html".format(folder, file)
        df.to_html(html_name)
    if export_csv:
        csv_name = "{}{}.csv".format(folder, file)
        df.to_csv(csv_name)
    return 1
