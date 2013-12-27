#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Import shapefile informations
from shapelib import ShapeFile
import dbflib
from shapely.geometry import Polygon

# Database
import pymongo

# Common
import csv
import time
import simplejson as json
from optparse import OptionParser

def loadMeasurements(datafile):
  connection = pymongo.Connection()
  db = connection.safecast
  locations = db.locations

  # Load data
  data = csv.reader(open(datafile))

  # Read the column names from the first line of the file
  fields = data.next()

  # Process data
  count = 0
  insertList = []
  start = time.time()
  end = time.time()
  for row in data:
    # Zip together the field names and values
    items = zip(fields, row)

    # Add the value to our dictionary
    item = {}
    for (name, value) in items:
       item[name] = value.strip()

    try:
      count+=1
      json = {'loc': {"Longitude" : float(item["Longitude"]), "Latitude" : float(item["Latitude"])},
            'cpm': float(item["Value"])
          }
      insertList.append(json)
    except:
      pass

    if len(insertList) > 5000:
        locations.insert(insertList)
        insertList = []

    if (count % 100000 == 0):
      end = time.time()
      print count, end - start
      start = time.time()

  print "Creating index ..."
  # locations.create_index([("loc", pymongo.GEOSPHERE)])
  locations.create_index([('loc', pymongo.GEO2D)])
  connection.disconnect()
  print "Done."

def swapCoordinates(data):
  new = []
  for d in data:
    new.append([d[1], d[0]])
  return new

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == '__main__':
  # Process command line options
  parser = OptionParser("Usage: safecastSummary.py [options] [measurements.csv]")
  parser.add_option("-l", "--load",
                    action="store_true", dest="load", default=False,
                    help="load measurements into database")

  (options, args) = parser.parse_args()

  if options.load:
    # Drop the old database if any
    connection = pymongo.Connection()
    connection.drop_database("safecast")
    connection.disconnect()
    if len(args) != 1:
      loadMeasurements("measurements.csv")
    else:
      loadMeasurements(args[0])

  # Connect to database
  connection = pymongo.Connection()
  db = connection.safecast
  locations = db.locations

  # GeoJSON countries
  # https://github.com/johan/world.geo.json/blob/master/countries.geo.json
  # {"type":"Feature","id":"AFG","properties":{"name":"Afghanistan"},"geometry":{"type":"Polygon","coordinates":[[[61.210817,35.650072],[62.230651,35.270664],[62.984662,35.404041],[63.193538,35.857166],[63.982896,36.00795] ... ]}},
  countries = json.loads(open("countries.geo.json").read())["features"]
  for country in countries:
    totalcount = 0
    name = country["properties"]["name"]
    polygonList = country["geometry"]["coordinates"]
    polygonType = country["geometry"]["type"]

    if polygonType == "Polygon":
      polygon = polygonList[0]
      cursors = locations.find({'loc': {'$within': { "$polygon" : swapCoordinates(polygon) }}})
      totalcount = cursors.count()
    else:
      for polygon in polygonList:
        if len(polygon) == 1:
          polygon = polygon[0]
        cursors = locations.find({'loc': {'$within': { "$polygon" : swapCoordinates(polygon) }}})
        totalcount = totalcount + cursors.count()

    if totalcount > 0:
      print "%s,%d" % (name, totalcount)
