#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from pylab import *
from mpl_toolkits.basemap import Basemap
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageChops
import simplejson as json
from matplotlib.collections import LineCollection
import matplotlib.patheffects as PathEffects
from matplotlib import cm
import time
from optparse import OptionParser

# Shapely
from shapely.geometry import Polygon

def drawMap(filename,names,totalCount):
  countries = json.loads(open(filename).read())["features"]

  for country in countries:
    name = country["properties"]["name"]
    polygonList = country["geometry"]["coordinates"]
    polygonType = country["geometry"]["type"]
    shpsegs = []

    print "Processing %s [%d/%s] ..." % (unicode(name).encode("utf-8"), len(polygonList), polygonType)
    maxverts = 0
    maxindex = 0
    counter = 0
    for polygon in polygonList:
      if polygonType == "MultiPolygon":
        for p in polygon:
          if len(p) == 1:
            p = p[0]
          if p[0] != p[-1]:
            p.append(p[0])

          lons, lats = zip(*p)
          x, y = m(lons, lats)
          shpsegs.append(zip(x,y))
          if len(x) > maxverts:
            maxverts = len(x)
            maxindex = counter
          counter+=1
      else:
        if len(polygon) == 1:
          polygon = polygon[0]
        if polygon[0] != polygon[-1]:
          polygon.append(polygon[0])

        lons, lats = zip(*polygon)
        x, y = m(lons, lats)
        shpsegs.append(zip(x,y))
        if len(x) > maxverts:
          maxverts = len(x)
          maxindex = counter
        counter+=1

    # Compute centroid
    centroid = Polygon(shpsegs[maxindex]).centroid

    # Create country shape
    lines = LineCollection(shpsegs,antialiaseds=(1,))
    lines.set_edgecolors('k')
    lines.set_linewidth(0.5)

    #import brewer2mpl
    #colormap = brewer2mpl.get_map('Paired', 'qualitative', 12).mpl_colors
    colormap = [(0.6509803921568628, 0.807843137254902, 0.8901960784313725), (0.12156862745098039, 0.47058823529411764, 0.7058823529411765), (0.6980392156862745, 0.8745098039215686, 0.5411764705882353), (0.2, 0.6274509803921569, 0.17254901960784313), (0.984313725490196, 0.6039215686274509, 0.6), (0.8901960784313725, 0.10196078431372549, 0.10980392156862745), (0.9921568627450981, 0.7490196078431373, 0.43529411764705883), (1.0, 0.4980392156862745, 0.0), (0.792156862745098, 0.6980392156862745, 0.8392156862745098), (0.41568627450980394, 0.23921568627450981, 0.6039215686274509), (1.0, 1.0, 0.6), (0.6941176470588235, 0.34901960784313724, 0.1568627450980392)]

    # Add color and label if covered by Safecast
    if name in names.keys():
      color = colormap[(int((float(names[name][0])/totalCount)*12)+1)]
      lines.set_label("%s - %0.1fK (%d)" % (name, names[name][0]/1000.0, names[name][1]) )
      #lines.set_label(name)
      lines.set_edgecolors(color)
      lines.set_facecolors(color)
      label = plt.text(centroid.x, centroid.y, "%d" % names[name][1], fontsize=5, ha='center', va='center', color='k', fontweight='bold')
      plt.setp(label, path_effects=[PathEffects.withStroke(linewidth=2, foreground="w")])
    ax.add_collection(lines)

def trim(im, border):
    bg = Image.new(im.mode, im.size, border)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    else:
        return im

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

  # Setup the figure
  fig = figure(figsize=(12,14), dpi=300)
  ax = plt.subplot(111)
  m = Basemap(projection='robin',lon_0=0,resolution='c')
  #m = Basemap(projection='merc',llcrnrlat=-80,urcrnrlat=80,llcrnrlon=-180,urcrnrlon=180,lat_ts=20,resolution='c')
  m.drawcountries(linewidth=0.1,color='w')
  m.drawparallels(np.arange(-90,90,10.), labels=[1,0,0,0], fontsize=5, dashes=[1,0], linewidth=0.2)
  m.drawmeridians(np.arange(-180.,181.,20.), labels=[0,0,0,1], fontsize=5, dashes=[1,0], linewidth=0.2)

  names = {}
  data = open(summaryFile, "r").readlines()
  totalCount = 0
  countryCount = 0
  for d in data[1:]:
    country, count = d.split(",")
    if int(count) > 10:
      countryCount+=1
      names[country[1:-1]] = (int(count), countryCount)
      totalCount += int(count)

  # Draw map
  drawMap("countries.geo.json",names,totalCount)

  # Add legend
  fontP = FontProperties()
  fontP.set_size('xx-small')
  lgd = plt.legend(loc='upper center', bbox_to_anchor=(0.5,-0.04), ncol=3,
    prop = fontP, fancybox = True, title='%d countries covered by Safecast' % len(names))
  lgd.get_title().set_fontsize('8')

  # Save map
  #mapFilename = time.strftime("%Y%m%d")+"_map"
  mapFilename = "map"
  fig.savefig(mapFilename+".png", bbox_extra_artists=(lgd,), transparent=True, bbox='tight', dpi=300)
  fig.savefig(mapFilename+".svg", bbox_extra_artists=(lgd,), transparent=True, bbox_inches='tight', pad_inches=0.25)
  trim(Image.open(mapFilename+".png"), (255,255,255,0)).save(mapFilename+".png")
  Image.open(mapFilename+".png").save(mapFilename+".jpg",quality=70) # create a 70% quality jpeg

  print "Total measurements =", totalCount
