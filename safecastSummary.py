#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Database
import pymongo

# Common
import csv
import time
import simplejson as json
from optparse import OptionParser

# -----------------------------------------------------------------------------
# Load the measurement into local mongodb (TokuMX with fractal tree index)
# -----------------------------------------------------------------------------
def loadMeasurements(datafile):
  print "Loading %s into the database ..." % datafile
  connection = pymongo.Connection()
  db = connection.safecast
  locations = db.locations

  # Load data
  data = csv.reader(open(datafile))

  # Read the column names from the first line of the file
  fields = data.next()

  # Process data
  count = 0
  failedCount = 0
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
      count += 1
      json = {'loc': {"Longitude" : float(item["Longitude"]),
                      "Latitude" : float(item["Latitude"])},
              'cpm': float(item["Value"])}
      insertList.append(json)
    except:
      failedCount += 1
      pass

    if len(insertList) > 5000:
        locations.insert(insertList)
        insertList = []

    if (count % 100000 == 0):
      end = time.time()
      print count, end - start
      start = time.time()

  if len(insertList):
    locations.insert(insertList)
  print "%d measurements processed (%d failed)" % (count, failedCount)

  print "Creating index ..."
  # locations.create_index([("loc", pymongo.GEOSPHERE)])
  locations.create_index([('loc', pymongo.GEO2D)])
  connection.disconnect()
  print "Done."

# -----------------------------------------------------------------------------
# Swap the latitude and longitude from the polygon provided from GeoJSON
# -----------------------------------------------------------------------------
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

  # Write output to CSV file
  csvfile = open("summary.csv", "wb")
  writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
  writer.writerow(["Country name", "Measurements"])

  # GeoJSON countries
  # from: https://github.com/johan/world.geo.json/blob/master/countries.geo.json
  countries = json.loads(open("countries.geo.json").read())["features"]
  for country in countries:
    totalcount = 0
    name = country["properties"]["name"]
    polygonList = country["geometry"]["coordinates"]
    polygonType = country["geometry"]["type"]

    print "Processing %s [%d] ..." % (name, len(polygonList))
    if polygonType == "Polygon":
      polygon = polygonList[0]
      cursors = locations.find({'loc': {'$within': {"$polygon": swapCoordinates(polygon)}}})
      totalcount = cursors.count()
    else:
      for polygon in polygonList:
        if len(polygon) == 1:
          polygon = polygon[0]
        cursors = locations.find({'loc': {'$within': {"$polygon": swapCoordinates(polygon)}}})
        totalcount = totalcount + cursors.count()

    if totalcount > 0:
      writer.writerow([name, totalcount])

  csvfile.close()
