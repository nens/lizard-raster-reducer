# -*- coding: utf-8 -*-
"""reporter to export aggregates to a file"""

import json
import pandas as pd
from lizard_raster_reducer.fetching import clean_unicode

pd.set_option("display.max_colwidth", -1)


def fill_alarm_reports(alarm_columns, df, date_times):
    """create and fill dataframes with alarm data"""
    report_count = pd.DataFrame()
    report_fraction = pd.DataFrame()
    for alarm_column in alarm_columns:
        for date_time in date_times:
            column_name = f"{alarm_column}_{date_time}"
            df_date = df.loc[df["datetime"] == date_time]
            total_area = round(sum(df_date["Area (ha)"]), 1)
            alarm_area = round(sum(df_date["Area (ha)"][df_date[alarm_column]]), 1)
            alarm_area_fraction = round(alarm_area / total_area, 2)
            report_fraction[column_name] = [alarm_area_fraction]
            region_count_alarm = sum(df_date[alarm_column])
            report_count[column_name] = [region_count_alarm]
    return report_fraction, report_count


def alarm_report(df, alarm_columns, file, slim=True):
    """small report to give insight in alarms"""
    date_times = list(df.datetime.unique())
    date_time = date_times[0]
    region_count = len(df.loc[df["datetime"] == date_time])
    report_fraction, report_count = fill_alarm_reports(alarm_columns, df, date_times)
    report_fraction.index = pd.Index(["Fraction of area"], name="index")
    report_count.index = pd.Index(["Number of regions"], name="index")
    fraction_report = report_fraction.T
    count_report = report_count.T
    fraction_alarm = fraction_report[fraction_report["Fraction of area"] > 0]
    count_alarm = count_report[count_report["Number of regions"] > 0]
    count_column = f"Number of regions / {region_count} regions"
    count_alarm = count_alarm.rename(
        {"Number of regions": count_column}, axis="columns"
    )
    report_alarm = fraction_alarm.join(count_alarm)

    report_alarm["index"] = report_alarm.index
    report_alarm[["Threshold", "Datetime"]] = report_alarm["index"].str.split(
        "_", expand=True
    )
    report_alarm = report_alarm.drop(columns=["index"])
    report_alarm = report_alarm.sort_values(
        by=["Threshold", "Datetime"], ascending=False
    )
    if slim:
        datetimes = list(report_alarm["Datetime"])
        report_alarm["Date"] = [datetime.split("T")[0] + "Z" for datetime in datetimes]
        report_alarm = report_alarm.drop(columns=["Datetime"])
    report_alarm = report_alarm.sort_index(axis=1)
    report_dict = report_alarm.to_dict(orient="records")
    export_files(report_dict, report_alarm, file, "alarms_")


def add_region_alarms(df, alarms):
    """add alarm columns to df. Column values become True/False dependent on thresholds"""
    raster_le, raster_ge = alarms
    columns = list(df.columns)
    class_columns = [c.split("_")[0] for c in columns if "_" in c]
    rasters = list(df.Raster.unique())
    data_columns = class_columns + rasters
    alarm_columns = []
    for data_column in data_columns:
        upper = f"{data_column} >= {str(raster_ge)}"
        lower = f"{data_column} <= {str(raster_le)}"
        for column in columns:
            if data_column in column:
                df[upper] = df[column] >= raster_ge
                df[lower] = df[column] <= raster_le
                alarm_columns.append(upper)
                alarm_columns.append(lower)

    return df, alarm_columns


def slim_aggregates(aggregates):
    """"slim version of the region aggregates, minimizing NoData and verbose naming"""
    slimmed_aggregates = []
    for aggregate in aggregates:
        verbose_keys = list(aggregate.keys())
        for verbose_key in verbose_keys:
            slim_key = verbose_key.split("_")[0]
            aggregate[slim_key] = aggregate.pop(verbose_key)
        datetime = aggregate["datetime"]
        aggregate["Date"] = datetime.split("T")[0] + "Z"
        aggregate.pop("datetime", None)
        slimmed_aggregates.append(aggregate)
    return slimmed_aggregates


def export_files(
    data_dict,
    pd_df,
    file,
    file_prefix,
    export_json=True,
    export_html=True,
    export_csv=True,
):
    folder = "reducer_results/"
    if export_html:
        html_name = f"{folder}{file_prefix}{file}.html"
        try:
            pd_df = pd_df.drop_duplicates()
            pd_df.to_html(html_name, index=False, index_names=False)
        except:
            html_df = clean_unicode(pd_df)
            html_df = html_df.drop_duplicates()
            html_df.to_html(html_name, index=False, index_names=False)
    if export_csv:
        csv_name = f"{folder}{file_prefix}{file}.csv"
        pd_df.to_csv(csv_name)
    if export_json:
        json_file = f"{folder}{file_prefix}{file}.json"
        with open(json_file, "w") as f:
            json.dump(data_dict, f)


def export(data_dict, file, export_json, export_html, export_csv, alarms, slim=True):
    """function to export aggregate data to disk in json, html or csv format"""
    pd_df = pd.DataFrame(data_dict)
    if alarms:
        alarm_df, alarm_columns = add_region_alarms(pd_df, alarms)
        alarm_report(alarm_df, alarm_columns, file)
    if slim:
        data_dict = slim_aggregates(data_dict)
        pd_df = pd.DataFrame(data_dict)
    if alarms:
        raster_le, raster_ge = alarms
        pd_df["alarm level <="] = raster_le
        pd_df["alarm level >="] = raster_ge
    export_files(data_dict, pd_df, file, "", export_json, export_html, export_csv)
    return 1
