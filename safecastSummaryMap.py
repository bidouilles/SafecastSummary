#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from pylab import *
from mpl_toolkits.basemap import Basemap
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageChops
import simplejson as json
from matplotlib.collections import LineCollection
from matplotlib import cm
import time


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

    # import brewer2mpl
    # colormap = brewer2mpl.get_map('Paired', 'qualitative', 8).mpl_colors
    colormap = [(0.6509803921568628, 0.807843137254902, 0.8901960784313725), (0.12156862745098039, 0.47058823529411764, 0.7058823529411765), (0.6980392156862745, 0.8745098039215686, 0.5411764705882353), (0.2, 0.6274509803921569, 0.17254901960784313), (0.984313725490196, 0.6039215686274509, 0.6), (0.8901960784313725, 0.10196078431372549, 0.10980392156862745), (0.9921568627450981, 0.7490196078431373, 0.43529411764705883), (1.0, 0.4980392156862745, 0.0)]

    if name in names.keys():
      color = colormap[(int((float(names[name])/totalCount)*8)+1)]
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
    if int(count) > 10:
      names[country[1:-1]] = int(count)
      totalCount += int(count)

  # Draw map
  drawMap("countries.geo.json",names,totalCount)

  # Add legend
  fontP = FontProperties()
  fontP.set_size('xx-small')
  lgd = plt.legend(loc='upper center', bbox_to_anchor=(0.5,-0.02), ncol=3,
    prop = fontP, fancybox = True, title='%d countries covered by Safecast' % len(names))
  lgd.get_title().set_fontsize('8')

  # Save map
  mapFilename = time.strftime("%Y%m%d")+"_map"
  fig.savefig(mapFilename+".png", bbox_extra_artists=(lgd,), bbox='tight')
  trim(Image.open(mapFilename+".png"), (255,255,255,255)).save(mapFilename+".png")
  Image.open(mapFilename+".png").save(mapFilename+".jpg",quality=70) # create a 70% quality jpeg

  print totalCount