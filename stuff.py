#!/usr/bin/env python


import json
import os
from enum import Enum


class Type(Enum):
  ROOT = 0
  BRANCH = 1

## TODO:
## - implement ijson for even more memory efficient access
## - feature: lookup tables for reappearing key/map names, which associate IDs to them which are automatically looked up when needed
class Dict:
  _root_store = 'root'
  _separator = '%'
  _name_store_depth = 'store_depth'
  _name_keys = 'keys'
  _suffix_meta = '.meta'
  
  def __init__(self, Name, MakeNew = False, StoreDepth = 1):
    self._name = Name
    self._type = None
    self._payload = {}
    self._cached_values = False
    self._store_depth = StoreDepth
    self._keys = None
    
    if MakeNew:
      if os.path.isdir(self._name) or os.path.isfile(self._name):
        print ('"'+self._name+'" already exists...')
        raise SystemExit
      else:
        os.system('mkdir -p '+self._name)
        self._set_root()
    else:
      ## Determine the Dict type
      self._determine_type()

    meta = self._retrieve_meta()
    if meta:
      self._keys = set(meta[Dict._name_keys])
      self._store_depth = meta[Dict._name_store_depth]
    else:
      self._keys = set()

  def _determine_type(self):
    if os.path.isdir(self._name):
      self._set_root()
    else:
      ## Far from being robust
      self._type = Type.BRANCH

  def _set_root(self):
    self._type = Type.ROOT
    ## Ensure that ROOT name ends with a "/"
    self._name = self._name.rstrip('/')+'/'

  def _retrieve_meta(self):
    name = self._get_meta_name()
    meta = None
    if os.path.isfile(name):
      with open(name, 'r') as inFile:
        meta = json.load(inFile)

    return meta

  def _get_meta_name(self):
    name = self._name
    if self._type == Type.ROOT:
      name += Dict._root_store
    name += Dict._suffix_meta

    return name

  def __getitem__(self, key):
    if key not in self._keys:
      print ('Key "'+str(key)+'" is not valid...')
      raise KeyError
    self._cache_values(key)

    return self._payload[key]

  def __setitem__(self, key, value):
    if key not in self._keys: self._keys.add(key)
    self._payload[key] = value

  def __contains__(self, item):
    if item in self._keys:
      return True
    else:
      return False

  def _get_path(self, name, suffix = ''):
    path = self._name
    if self._type != Type.ROOT:
      path += Dict._separator
    path += name+suffix
      
    return path

  def _cache_values(self, key):
    if key in self._payload:
      return
    name = self._get_path(key)
    if os.path.isfile(name):
      with open(name, 'r') as inFile:
        self._payload[key] = json.load(inFile)
    else:
      self._payload[key] = Dict(name)

  def _cache_all_values(self):
    if self._cached_values: return
    for key in self._keys:
      self._cache_values(key)
    self._cached_values = True

  def keys(self):
    return self._keys

  def values(self):
    self._cache_all_values()
    
    return self._payload.values()

  def items(self):
    self._cache_all_values()
    
    return self._payload.items()

  def clear(self):
    self._cached_values = False
    self._payload = {}

  def write(self, clear = True):
    if self._type != Type.ROOT:
      print ('This is not a Dict of type ROOT, cannot write to file...')
      raise SystemExit
    if self._type == Type.ROOT and not os.path.isfile(self._name+Dict._root_store+Dict._suffix_meta):
      Dict.dump(self._payload, self._name, self._store_depth, True)
      if clear: self.clear()
    else:
      self._update()

  def _update(self):
    self._update_keys()
    for key in self._payload.keys():
      if isinstance(self._payload[key], Dict):
        self._payload[key]._update()
      else:
        name = self._get_path(key, Dict._separator)
        Dict._generate_output(self._payload[key], name, self._store_depth-1)

  def _update_keys(self):
    meta = self._retrieve_meta()
    if not meta:
      print ('No meta file found, abort...')
      raise SystemExit
    meta[Dict._name_keys] = list(self._keys)
    name = self._get_meta_name()
    with open(name, 'w') as outFile:
      json.dump(meta, outFile)

  @staticmethod
  def dump(obj, name, store_depth, append):
    if store_depth < 0:
      print ('Negative store depth is not supported, abort...')
      raise SystemExit
    if not append and os.path.isdir(name): os.system('rm -r '+name)
    os.system('mkdir -p '+name)
    name = name.rstrip('/')+'/'
    Dict._generate_output(obj, name, store_depth)

  @staticmethod
  def _generate_output(obj, name, store_depth):
    if store_depth < 0:
      print ('Store depth is negative, abort...')
      raise SystemExit
    sep = Dict._separator
    if store_depth > 0:
      if isinstance(obj, dict):
        ## Generate meta file for this dict
        meta_store = None
        meta_suffix = Dict._suffix_meta
        if not name.endswith(sep):
          meta_store = name+Dict._root_store+meta_suffix
        else:
          meta_store = name.rstrip(sep)+meta_suffix
        with open(meta_store, 'w') as outFile:
          meta = { Dict._name_keys: list(obj.keys()), Dict._name_store_depth: store_depth }
          json.dump(meta, outFile)
        store_depth -= 1
        for key, val in obj.items():
          sub_name = name+key.replace(' ', '_')+sep
          Dict._generate_output(val, sub_name, store_depth)
      else:
        name = name.rstrip(sep)
        with open(name, 'w') as outFile:
          json.dump(obj, outFile)
    else:
      name = name.rstrip(sep)
      with open(name, 'w') as outFile:
        json.dump(obj, outFile)


## TODO: should probably throw an exception if the obj is not a str, otherwise we run into problems if one tries to use jsonx.Dict functionalities directly
## Maybe encapsulate everything such that it can be used exactly as a json dict and writing to disk is seemingless
def load(obj):
  data = None
  if isinstance(obj, str):
    if os.path.isdir(obj):
      data = Dict(Name = obj)
    else:
      print ('Input not found...')
      raise SystemExit
  else:
    ## If input is not a string, assume that it's a file-type object, just load as json file in this case
    data = json.load(obj)
    
  return data

def dump(obj, name, store_depth = 1, append = False):
  ## name is either a file-like object, then just dump a normal json file
  ## Else, if it's the name of a file on disk, throw an exception
  ## If not, then build a Dict with name as the name of the root folder
  ## Need a seemingless appending if folder already exists (with a required meta-file in the root folder maybe, otherwise exception)
  ## Obviously also need a switch for overwrite
  if not isinstance(store_depth, int):
    print ('Store depth is not integer...')
    raise TypeError
  if isinstance(name, str):
    Dict.dump(obj, name, store_depth, append)
  else:
    json.dump(obj, name)
