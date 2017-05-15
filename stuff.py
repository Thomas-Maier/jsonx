#!/usr/bin/env python


import json
import os
import glob
from enum import Enum


class Type(Enum):
  ROOT = 0
  BRANCH = 1

class ImprovedJsonDict:
  root_key_store = 'root'
  separator = '%'
  
  def __init__(self, InputName):
    self._name = InputName
    self._type = None
    self._determine_type()
    self._payload = {}
    self._cached_values = False
    self._separator = ImprovedJsonDict.separator

    key_store = None
    if self._type == Type.ROOT:
      self._name = self._name.rstrip('/')+'/'
      key_store = self._name+ImprovedJsonDict.root_key_store+'.keys'
    else:
      key_store = self._name.rstrip(self._separator)+'.keys'
    self._keys = None
    with open(key_store, 'r') as inFile:
      self._keys = set(json.load(inFile))
      
    return None

  def _determine_type(self):
    if os.path.isdir(self._name):
      self._type = Type.ROOT
    else:
      ## Far from being robust
      self._type = Type.BRANCH
      
    return 0

  def __getitem__(self, key):
    if key not in self._keys:
      print ('Key "'+key+'" is not valid...')
      raise KeyError
    self._cache_values(key)

    return self._payload[key]

  def __setitem__(self, key, value):
    if key not in self._keys: self._keys.add(key)
    self._payload[key] = value

  def _cache_values(self, key):
    ## This is not super robust (also latter part only necessary for the clear cache hack)
    if key in self._payload and self._payload[key]: return
    name = self._name
    if self._type != Type.ROOT:
      name += self._separator
    name += key

    if os.path.isfile(name):
      with open(name, 'r') as inFile:
        self._payload[key] = json.load(inFile)
    else:
      self._payload[key] = ImprovedJsonDict(name)

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

  @staticmethod
  def dump(obj, name, store_depth, append):
    if not append and os.path.isdir(name): os.system('rm -r '+name)
    os.system('mkdir -p '+name)
    name = name.rstrip('/')+'/'
    ImprovedJsonDict._generate_output(obj, name, store_depth)

  @staticmethod
  def _generate_output(obj, name, store_depth):
    sep = ImprovedJsonDict.separator
    if store_depth > 0:
      if isinstance(obj, dict):
        ## Generate keys file for this dict
        key_store = None
        if not name.endswith(sep):
          key_store = name+ImprovedJsonDict.root_key_store+'.keys'
        else:
          key_store = name.rstrip(sep)+'.keys'
        with open(key_store, 'w') as outFile:
          json.dump(list(obj.keys()), outFile)
        store_depth -= 1
        for key, val in obj.items():
          sub_name = name+key.replace(' ', '_')+sep
          ImprovedJsonDict._generate_output(val, sub_name, store_depth)
      else:
        name = name.rstrip(sep)
        with open(name, 'w') as outFile:
          json.dump(obj, outFile)
    else:
      name = name.rstrip(sep)
      with open(name, 'w') as outFile:
        json.dump(obj, outFile)


def load(obj):
  data = None
  if isinstance(obj, str):
    if os.path.isdir(obj):
      data = ImprovedJsonDict(InputName = obj)
    else:
      print ('Input not found...')
      raise SystemExit
  else:
    ## If input is not a string, assume that it's a file-type object, just load as json file in this case
    data = json.load(obj)
    
  return data

def dump(obj, name, store_depth = 1, append = False):
  ## name is either a file-like object, then just dump a normal json file
  ## Else, if it's the name of a file on disk, through an exception
  ## If not, then build an ImprovedJsonDict with name as the name of the root folder
  ## Need a seemingless appending if folder already exists (with a required meta-file in the root folder maybe, otherwise exception)
  ## Obviously also need a switch for overwrite
  if not isinstance(store_depth, int):
    print ('Store depth is not integer...')
    raise TypeError
  if isinstance(name, str):
    ImprovedJsonDict.dump(obj, name, store_depth, append)
  else:
    json.dump(obj, name)
