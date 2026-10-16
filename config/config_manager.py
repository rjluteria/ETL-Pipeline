"""
config_manager.py

Do's:
    This is the only file that reads and writes config.json.
    If any other file needs data from the config, it must call
    a function from here instead of opening config.json directly.

Dont's:
    - Any data processing
    - Any UI logic
"""
#import dependencies
import json
import os
import sys

def get_config_path(): #get the path to config.json, whether we're running from source or from a frozen executable
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        base = os.path.dirname(base)
    return os.path.join(base, "config.json")

def read_config(): #read config.json and return it as a dictionary
    path = get_config_path()
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def save_config(data): #save a dictionary to config.json
    path = get_config_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
def get_stations(): #read stations from config and return them as a dictionary
    return read_config().get("stations", {})

def save_stations(stations): #read stations from config and save them to config
    config = read_config()
    config["stations"] = stations
    save_config(config)

def get_groups(): #read groups from config and return them as a dictionary
    return read_config().get("groups", {})

def save_groups(groups): #read groups from config and save them to config
    config = read_config()
    config["groups"] = groups
    save_config(config)

def get_billing(): #read billing from config and return it as a dictionary
    return read_config().get("billing", {})

def save_billing(billing): #read billing from config and save it to config
    config = read_config()
    config["billing"] = billing
    save_config(config)

def get_charging_points(): #read charging points from config and return them as a dictionary
    return read_config().get("charging_points", {})

def save_charging_points(charging_points): #read charging points from config and save them to config
    config = read_config()
    config["charging_points"] = charging_points
    save_config(config)

def get_station_blacklist(): #blacklist of stations to ignore when fetching data, read from config and return it as a list
    return read_config().get("station_blacklist", []) 

def get_cutoff_date(): #cutoff date for fetching data, read from config and return it as a string in the format "YYYY-MM-DD", default is "2024-06-24"
    return read_config().get("cutoff_date", "2024-06-24")

def get_station_normalization():
    # Station prefixes whose trailing "(private)" marker should be removed.
    return read_config().get("station_normalization", [])
