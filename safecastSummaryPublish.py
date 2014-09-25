#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import time
from optparse import OptionParser
import gspread

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__=='__main__':
  # Process command line options
  parser = OptionParser("Usage: safecastSummaryMap.py [summary.csv]")
  (options, args) = parser.parse_args()

  if len(args) != 1:
    summaryFile = "summary.csv"
  else:
    summaryFile = args[0]

  names = {}
  data = open(summaryFile, "r").readlines()
  totalCount = 0
  countryCount = 0
  for d in data[1:]:
    country, count = d.split(",")
    if int(count) > 200:
      countryCount+=1
      names[country[1:-1]] = (int(count), countryCount)
      totalCount += int(count)

  print "Total measurements =", totalCount

  # Login with your Google account
import getpass
print "Login into Google Docs"
pw = getpass.getpass()
gc = gspread.login('lbergeret@gmail.com', pw)

# Open a worksheet from spreadsheet with one shot
worksheet = gc.open("SafecastSummary").sheet1

# Find today column
date_list = worksheet.range('A1:Z1')
date_column = 1
for cell in date_list:
  if cell.value == None:
    worksheet.update_cell(1, date_column, time.strftime("%Y%m%d"))
    break
  date_column+=1

# Fetch a cell range
cell_list = worksheet.range('A2:A%d'% (len(names)+1))
countries = names.keys()
countries.sort()

for name in countries:
  try:
    countryCell = worksheet.find(name)
    worksheet.update_cell(countryCell.row, date_column, names[name][0])
  except:
    # find a position
    print name
    for cell in cell_list:
      if cell.value == None:
        cell.value = name
        worksheet.update_cell(cell.row, date_column, names[name][0])
        break

worksheet.update_cells(cell_list)
