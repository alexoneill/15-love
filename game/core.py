#!/usr/bin/python2
# core.py
# aoneill - 04/10/17

import sys
import random
import time

import pauschpharos as PF
import lumiversepython as L

SEQ_LIM = 200

def memoize(ignore = None):
  if(ignore is None):
    ignore = set()

  def inner(func):
    cache = dict()

    def wrapper(*args):
      memo = tuple(filter(lambda x: x,
                     map(lambda (i, e):
                       e if (i not in ignore)
                         else None,
                       enumerate(args))))

      if(memo not in cache):
        cache[memo] = func(*args)

      return cache[memo]
    return wrapper
  return inner

def blank():
  p = PF.PauschPharos()
  p.SetBlank()
  p.Trigger(PF.DEFAULT_ID, None)

def fireplace(rig):
  # Warm up cache
  for seq in xrange(SEQ_LIM):
    query(rig, '$sequence=%d' % seq)

def init(upload = True, run = True, wipe = True, fire = True):
  rig = L.Rig("/home/teacher/Lumiverse/PBridge.rig.json")
  rig.init()

  # Upload the blank template
  if(upload):
    blank()

  # Run if requested
  if(run):
    rig.run()

  # Wipe if requested
  if(wipe):
    for seq in xrange(SEQ_LIM):
      query(rig, '$sequence=%d' % seq).setRGBRaw(0, 0, 0)

  # Heat up the cache
  if(fire and not wipe):
    fireplace(rig)

  return rig

@memoize(ignore = set([0]))
def query(rig, text):
  return rig.select(text)

def seq(rig, num):
  return query(rig, '$sequence=%d' % num)

def rand_color():
  func = lambda: random.randint(0, 255) / 255.0
  return (func(), func(), func())
