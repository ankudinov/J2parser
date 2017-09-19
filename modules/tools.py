import yaml
from time import time as time                   # used in: time_stamp()
from datetime import datetime as datetime       # used in: time_stamp()
import json

__author__ = 'Petr Ankudinov, pa@arista.com'


def merge_dict(d1, d2):
    """
    Merge 2 dictionaries together, keeping every element with unique key sequence.
    Relies on recursion.
    :param d1: Primary dictionary.
    :param d2: Secondary dictionary. If element is already present in d1, conflicting element from d1 will be replaced.
    :return: Combined dictionary. All elements from d1 and elements from d2 if missing in d1.
    """
    result = dict()
    all_keys = set(d1.keys()).union(d2.keys())
    for key in all_keys:
        if key not in d1.keys():
            result[key] = d2[key]
        elif key not in d2.keys():
            result[key] = d1[key]
        else:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    result[key] = merge_dict(d1[key], d2[key])  # recursion
            elif isinstance(d1[key], list) or isinstance(d2[key], list):
                temp_set = set()
                temp_dict = dict()

                if isinstance(d1[key], dict):
                    temp_dict = merge_dict(temp_dict, d1[key])  # recursion
                if isinstance(d2[key], dict):
                    temp_dict = merge_dict(temp_dict, d2[key])  # recursion

                if isinstance(d1[key], list):
                    for e1 in d1[key]:
                        if isinstance(e1, dict):
                            temp_dict = merge_dict(temp_dict, e1)  # recursion
                        else:
                            temp_set.add(e1)

                if isinstance(d2[key], list):
                    for e2 in d2[key]:
                        if isinstance(e2, dict):
                            temp_dict = merge_dict(temp_dict, e2)  # recursion
                        else:
                            temp_set.add(e2)

                result[key] = list()
                result[key].append(temp_dict)
                for e in temp_set:
                    result[key].append(e)
            else:
                result[key] = d2[key]

    return result


def build_dict(key_list, value):
    """
    Build a hierarchical dictionary with a single element from the list of keys and a value.
    :param key_list: List of dictionary element keys.
    :param value: Key value.
    :return: dictionary
    """
    temp_dict = {}
    if key_list:
        key = key_list.pop()
        temp_dict[key] = build_dict(key_list, value)  # recursion
        return temp_dict
    else:
        return value


def load_yaml(filename):
    # can be used to check if file is YAML as well
    try:
        file = open(filename, mode='r')
    except Exception as _:
        print('ERROR: Can not open ', filename)
        raise SystemExit(0)
    else:
        try:
            yaml_data = yaml.load(file)
            file.close()
        except Exception as _:
            return False
        else:
            return yaml_data


def time_stamp():
    """
    time_stamp function can be used for debugging or to display timestamp for specific event to a user
    :return: returns current system time as a string in Y-M-D H-M-S format
    """
    time_not_formatted = time()
    time_formatted = datetime.fromtimestamp(time_not_formatted).strftime('%Y-%m-%d:%H:%M:%S.%f')
    return time_formatted
