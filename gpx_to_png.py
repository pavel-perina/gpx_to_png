# -*- coding: utf-8 -*-

import sys as mod_sys
import math as mod_math
import logging as mod_logging
import urllib as mod_urllib
import os as mod_os
import gpxpy as mod_gpxpy
from PIL import Image as mod_pil_image
from PIL import ImageDraw as mod_pil_draw
import glob as mod_glob
osm_base_url = "http://a.tile.opencyclemap.org/cycle"
osm_cache_base = r"c:\devel-python\.cache\opencyclemap"
osm_tile_res = 256

def format_time(time_s):
    if not time_s:
        return 'n/a'
    minutes = mod_math.floor(time_s / 60.)
    hours = mod_math.floor(minutes / 60.)
    return '%s:%s:%s' % (str(int(hours)).zfill(2), str(int(minutes % 60)).zfill(2), str(int(time_s % 60)).zfill(2)) 

def get_tile_url (x, y, z):
#    return "http://a.tile.opencyclemap.org/cycle/%d/%d/%d.png" % (z, x, y)
    return "http://m1.mapserver.mapy.cz/turist_trail-m/%d-%d-%d" % (z, x, y)
#    return "http://geoportal-rm.cuzk.cz/WMTS_ZM_900913/WMTService.aspx?service=WMTS&request=GetTile&version=1.0.0&layer=ZM&style=default&format=image/png&TileMatrixSet=googlemapscompatibleext2:epsg:3857&TileMatrix=%d&TileRow=%d&TileCol=%d" % (z, y, x)


def get_tile_filename (x, y, z):
#   return r"c:\devel-python\.cache\opencyclemap\%d\%d\%d.png" % (z, x, y)
    return r"c:\devel-python\.cache\seznam-turist-trail\%d\%d\%d.png" % (z, x, y)
#    return r"c:\devel-python\.cache\cuzk-zm\%d\%d\%d.png" % (z, y, x)

def get_map_suffix ():
#    return "osm-cycle"
    return "seznam-turist"
#    return "cuzk"

def osm_lat_lon_to_x_y_tile (lat_deg, lon_deg, zoom):
    """ Gets tile containing given coordinate at given zoom level """
    # taken from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames, works for OSM maps and mapy.cz
    lat_rad = mod_math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - mod_math.log(mod_math.tan(lat_rad) + (1 / mod_math.cos(lat_rad))) / mod_math.pi) / 2.0 * n)
    return (xtile, ytile)


def osm_get_auto_zoom_level ( min_lat, max_lat, min_lon, max_lon, max_n_tiles):
    """ Gets zoom level which contains at maximum `max_n_tiles` """
    for z in range (0,17):
        x1, y1 = osm_lat_lon_to_x_y_tile (min_lat, min_lon, z)
        x2, y2 = osm_lat_lon_to_x_y_tile (max_lat, max_lon, z)
        max_tiles = max (abs(x2 - x1), abs(y2 - y1))
        if (max_tiles > max_n_tiles):
            print ("Max tiles: %d" % max_tiles)
            return z 
    return 17
    

def osm_cache_tile (x,y,z):
    """ Downloads tile x,y,x into cache. Directories are automatically created, existing files are not retrieved. """
    src_url = get_tile_url(x,y,z)
    dst_filename = get_tile_filename(x,y,z)
    
    dst_dir = mod_os.path.dirname(dst_filename)
    if not mod_os.path.exists(dst_dir):
        mod_os.makedirs(dst_dir)    
    if mod_os.path.isfile (dst_filename):
        return
            
    print ("Downloading %s ..." % src_url)
    request = mod_urllib.request.Request (src_url)
    response = mod_urllib.request.urlopen (request)
    data = response.read();    
    f = open(dst_filename, "wb")
    f.write(data)
    f.close()

        
class MapCreator:
    """ Class for map drawing """

    def __init__(self, min_lat, max_lat, min_lon, max_lon, z):
        """ constructor """
        x1, y1 = osm_lat_lon_to_x_y_tile (min_lat, min_lon, z)
        x2, y2 = osm_lat_lon_to_x_y_tile (max_lat, max_lon, z)
        self.x1 = min (x1, x2)
        self.x2 = max (x1, x2)
        self.y1 = min (y1, y2)
        self.y2 = max (y1, y2)
        self.w = (self.x2 - self.x1 + 1) * osm_tile_res
        self.h = (self.y2 - self.y1 + 1) * osm_tile_res
        self.z = z
        print (self.w, self.h)
        self.dst_img = mod_pil_image.new ("RGB", (self.w, self.h))


    def cache_area(self):
        """ Downloads necessary tiles to cache """
        print ("Caching tiles x1=%d y1=%d x2=%d y2=%d" % (self.x1, self.y1, self.x2, self.y2))
        for y in range (self.y1, self.y2 + 1):
            for x in range (self.x1, self.x2 + 1):
                osm_cache_tile (x, y, self.z)


    def create_area_background(self):
        """ Creates background map from cached tiles """        
        for y in range (self.y1, self.y2+1):
            for x in range (self.x1, self.x2+1):
                try:
                    src_img = mod_pil_image.open (get_tile_filename (x, y, z))
                    dst_x = (x-self.x1)*osm_tile_res
                    dst_y = (y-self.y1)*osm_tile_res
                    self.dst_img.paste (src_img, (dst_x, dst_y))
                except Exception as e:
                    print("Error processing file " + get_tile_filename (x, y, z))


    def lat_lon_to_image_xy (self, lat_deg, lon_deg):
        """ Internal. Converts lat, lon into dst_img coordinates in pixels """
        lat_rad = mod_math.radians(lat_deg)
        n = 2.0 ** self.z
        xtile_frac = (lon_deg + 180.0) / 360.0 * n
        ytile_frac = (1.0 - mod_math.log(mod_math.tan(lat_rad) + (1 / mod_math.cos(lat_rad))) / mod_math.pi) / 2.0 * n
        img_x = int( (xtile_frac-self.x1)*osm_tile_res )
        img_y = int( (ytile_frac-self.y1)*osm_tile_res )
        return (img_x, img_y)


    def draw_track (self, gpx):
        """ Draw GPX track onto map """
        draw = mod_pil_draw.Draw (self.dst_img)
        trk = 0         # Just changes color of segment a little
        for track in gpx.tracks:
            for segment in track.segments:
                idx = 0
                x_from = 0
                y_from = 0
                for point in segment.points:
                    if (idx == 0):
                        x_from, y_from = self.lat_lon_to_image_xy (point.latitude, point.longitude)
                    else:
                        x_to, y_to = self.lat_lon_to_image_xy (point.latitude, point.longitude)
#                        draw.line ((x_from,y_from,x_to,y_to), (255,0,trk), 2)
                        draw.line ((x_from,y_from,x_to,y_to), (0,0,0), 3)
                        x_from = x_to
                        y_from = y_to
                    idx += 1
                trk += 32
                if (trk > 160):
                    trk = 0
                    

    def save_image(self, filename):
        print("Saving " + filename) 
        self.dst_img.save (filename)
        
if (__name__ == '__main__'):
    """ Program entry point """

    #gpx_files = mod_sys.argv[1:]
    #if not gpx_files:
    #    print('No GPX files given')
    #    mod_sys.exit(1)

    gpx_files = mod_glob.glob (r"c:\devel-python\.tracks\201509*.gpx")

    for gpx_file in gpx_files:
        try:
            gpx = mod_gpxpy.parse(open(gpx_file))

            # Print some track stats
            print ('--------------------------------------------------------------------------------')
            print ('  GPX file     : %s' % gpx_file)
            start_time, end_time = gpx.get_time_bounds()
            print('  Started       : %s' % start_time)
            print('  Ended         : %s' % end_time)
            print('  Length        : %2.2fkm' % (gpx.length_3d() / 1000.))
            moving_time, stopped_time, moving_distance, stopped_distance, max_speed = gpx.get_moving_data()
            print('  Moving time   : %s' % format_time(moving_time))
            print('  Stopped time  : %s' % format_time(stopped_time))
#            print('  Max speed     : %2.2fm/s = %2.2fkm/h' % (max_speed, max_speed * 60. ** 2 / 1000.))    
            uphill, downhill = gpx.get_uphill_downhill()
            print('  Total uphill  : %4.0fm' % uphill)
            print('  Total downhill: %4.0fm' % downhill)
            min_lat, max_lat, min_lon, max_lon = gpx.get_bounds()
            print("  Bounds        : [%1.4f,%1.4f,%1.4f,%1.4f]" % (min_lat, max_lat, min_lon, max_lon))
            z = osm_get_auto_zoom_level (min_lat, max_lat, min_lon, max_lon, 6)
            print("  Zoom Level    : %d" % z)

            # Create the map
            map_creator = MapCreator (min_lat, max_lat, min_lon, max_lon, z)
            map_creator.cache_area()
            map_creator.create_area_background()
            map_creator.draw_track(gpx)
            map_creator.save_image (gpx_file[:-4] + '-' + get_map_suffix() + '.png')

        except Exception as e:
            mod_logging.exception(e)
            print('Error processing %s' % gpx_file)
            mod_sys.exit(1) 
