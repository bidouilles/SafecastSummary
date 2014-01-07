#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from pylab import *
from mpl_toolkits.basemap import Basemap
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageChops
import simplejson as json
from matplotlib.collections import LineCollection
from matplotlib import cm

def drawMap(filename,names,totalCount):
  countries = json.loads(open(filename).read())["features"]

  for country in countries:
    name = country["properties"]["name"]
    polygonList = country["geometry"]["coordinates"]
    polygonType = country["geometry"]["type"]
    shpsegs = []

    print "Processing %s [%d/%s] ..." % (unicode(name).encode("utf-8"), len(polygonList), polygonType)
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
      else:
        if len(polygon) == 1:
          polygon = polygon[0]
        if polygon[0] != polygon[-1]:
          polygon.append(polygon[0])

        lons, lats = zip(*polygon)
        x, y = m(lons, lats)
        shpsegs.append(zip(x,y))

    lines = LineCollection(shpsegs,antialiaseds=(1,))
    lines.set_edgecolors('k')
    lines.set_linewidth(0.5)

    if name in names.keys():
      color = cm.jet(float(names[name])/totalCount)
      lines.set_label("%s (%0.1fK)" % (name, names[name]/1000.0) )
      #lines.set_label(name)
      lines.set_edgecolors(color)
      lines.set_facecolors(color)
    ax.add_collection(lines)

def trim(im, border):
    bg = Image.new(im.mode, im.size, border)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    else:
        return im

if __name__=='__main__':
  fig = figure(figsize=(12,14), dpi=300)
  ax = plt.subplot(111)
  m = Basemap(projection='robin',lon_0=0,resolution='c')
  m.drawcountries(linewidth=0.1,color='w')

  names = {}
  data = open("summary.csv", "r").readlines()
  totalCount = 0
  for d in data[1:]:
    country, count = d.split(",")
    if int(count) > 100:
      names[country[1:-1]] = int(count)
      totalCount += int(count)

  # Draw map
  drawMap("countries.geo.json",names,totalCount)

  # Add legend
  fontP = FontProperties()
  fontP.set_size('xx-small')
  lgd = plt.legend(loc='upper center', bbox_to_anchor=(0.5,-0.02), ncol=3,
    prop = fontP, fancybox = True, title='Countries covered by Safecast')
  lgd.get_title().set_fontsize('8')

  # Save map
  fig.savefig("map.png", bbox_extra_artists=(lgd,), bbox='tight')
  trim(Image.open("map.png"), (255,255,255,255)).save("map.png")
