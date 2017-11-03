# gpx_to_png

# Motivation to write and use it
I become lazy to download tracks from my old Garmin GPS regularly so they piled up in SD card's root directory and was impossible to browse and sort in some convenient way. So I created this simple script that creates images from all GPX files in a directory in one go.

# Prerequisites
- basic Python knowledge
- gpxpy https://pypi.python.org/pypi/gpxpy
- pillow https://pypi.python.org/pypi/Pillow

# Description
- iterates through GPX files matching hard-coded mask
- downloads (steals) map tiles of location into the hard-coded cache directory (works with osm.org or mapy.cz)
- creates the image with the map of area
- draws track segments from GPX files
- saves the image

# Notes
- few things are hardcoded at different places, sorry for that

# Result (example)
![20120812.png](http://i.imgur.com/NU9OcGb.png)
