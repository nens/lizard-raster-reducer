#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
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
    pool = ThreadPool(processes=8)
    url_json_dicts = pool.map(request_url_json_dict_from_url, urls)
    pool.close()
    pool.join()
    return url_json_dicts


def select_from_list(itemlist, help_text="Which item (enter_number)?"):
    """select item from list of items, based on user input"""
    index_number = 0
    numbered_itemlist = []
    for counter, item in enumerate(itemlist):
        numbered_item = "{}: {} ".format(counter + 1, item)
        numbered_itemlist.append(numbered_item)
    print("\n".join([item for item in numbered_itemlist]))
    false_input = True
    while false_input:
        try:
            item_number = input("{}\n".format(help_text))
            while not item_number.isnumeric():
                item_number = input("{}\n".format(help_text))
            index_number = int(item_number) - 1
            selected_item = itemlist[index_number]
            false_input = False
        except:
            false_input = True
    return selected_item, index_number


def unpickle(file):
    """load pickle file from cache"""
    if os.path.isfile(file):
        return pickle.load(open(file, "rb"))
    else:
        return None


def flatten(items, seqtypes=(list, tuple)):
    """convert nested list to flat list"""
    for c, item in enumerate(items):
        while c < len(items) and isinstance(items[c], seqtypes):
            items[c : c + 1] = items[c]
    return items
