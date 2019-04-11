#!/usr/bin/env python
# -*- coding: utf-8 -*-
""""Functions to fetch and parse data"""

import os
import logging
import numpy as np
import pandas as pd
import pickle
import requests
import urllib.parse as urlparse

from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)

REQUESTS_HEADERS = {}


def get_headers():
    """return headers"""
    return REQUESTS_HEADERS


def set_headers(username, password):
    """set Lizard login credentials"""
    REQUESTS_HEADERS["username"] = username
    REQUESTS_HEADERS["password"] = password
    REQUESTS_HEADERS["Content-Type"] = "application/json"


def request_json_from_url(url, params={}):
    """retrieve json object from url"""
    params["format"] = "json"
    r = requests.get(url=url, params=params, headers=get_headers())
    r.raise_for_status()
    return r.json()


def request_url_json_dict_from_url(url, params={}):
    """retrieve dict with url and fetched json object from url"""
    params["format"] = "json"
    r = requests.get(url=url, params=params, headers=get_headers())
    r.raise_for_status()
    return {url: r.json()}


def parameterised_url(url, params):
    """generate specific url query from base url and parameters"""
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlparse.urlencode(query)
    url = urlparse.urlunparse(url_parts)
    return url


def get_json_objects_async(urls):
    """retrieve a dict with urls and corresponding jsons.
     The data is fetched asynchronously to speed up the process."""
    pool = ThreadPool(processes=4)
    url_json_dicts = pool.map(request_url_json_dict_from_url, urls)
    pool.close()
    pool.join()
    return url_json_dicts


# TODO find out how to mimic user input for test function
# def select_from_list(item_list, help_text="Which item (enter_number)?"):
#     """select item from list of items, based on user input"""
#     index_number = 0
#     numbered_item_list = []
#     for counter, item in enumerate(item_list):
#         numbered_item = f"{counter + 1}: {item} "
#         numbered_item_list.append(numbered_item)
#     print("\n".join([item for item in numbered_item_list]))
#     false_input = True
#     while false_input:
#         try:
#             item_number = input(f"{help_text}\n")
#             while not item_number.isnumeric():
#                 item_number = input(f"{help_text}\n")
#             index_number = int(item_number) - 1
#             selected_item = item_list[index_number]
#             false_input = False
#         except:
#             false_input = True
#     return selected_item, index_number


def unpickle(file):
    """load pickle file from cache"""
    if os.path.isfile(file):
        return pickle.load(open(file, "rb"))
    else:
        return None


def flatten(items, seq_types=(list, tuple)):
    """convert nested list to flat list"""
    for c, item in enumerate(items):
        while c < len(items) and isinstance(items[c], seq_types):
            items[c : c + 1] = items[c]
    return items


def clean_unicode(df):
    """clean df"""
    # Transforms the DataFrame to Numpy array
    df_columns = list(df.columns)
    df = df.values
    # Encode all strings with special characters
    for x in np.nditer(df, flags=["refs_ok"], op_flags=["copy", "readonly"]):
        df[df == x] = str(str(x).encode("latin-1", "replace").decode("utf8"))
    # Transform the Numpy array to Dataframe again
    df = pd.DataFrame(df)
    df.columns = [column.encode() for column in df_columns]
    return df
