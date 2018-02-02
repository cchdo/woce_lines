
# coding: utf-8

# In[6]:


from csv import DictReader
from pathlib import Path
from collections import deque

from shapely.geometry import LineString
from shapely.ops import transform, linemerge

file = Path("WHP_Sections.gzt")


whp_sections = {}

def gridwrap(x, y, z=None):
    while x > 180:
        x = x - 360
    return (x, y)

with file.open() as f:
    for l in f:
        if l.startswith("%"):
            continue
        if l.startswith("Feature"):
            break
        print(l)
    reader = DictReader(f, fieldnames=["Feature", "Type"], restkey="positions", delimiter=";")
    for l in reader:
        numeric_pts = deque([float(i) for i in l["positions"] if len(i)>0])
        
        num_pts = int(numeric_pts.popleft())
        geom = LineString([[numeric_pts.popleft(), numeric_pts.popleft()] for _ in range(num_pts)])
        geom = transform(gridwrap, geom)
        try:
            num_pts = int(numeric_pts.popleft())
            seg2 = LineString([[numeric_pts.popleft(), numeric_pts.popleft()] for _ in range(num_pts)])
            seg2 = transform(gridwrap, seg2)
            geom = linemerge([geom, seg2])
        except IndexError:
            # not all lines have a second segment
            pass
        whp_sections[l["Feature"]] = geom


# In[17]:


from shapely.geometry import MultiLineString
from shapely.ops import split, transform
import geojson

antimeridian = LineString([(180,90), (180,-90)])

def t(x, y, z=None):
    x = (x + 360) % 360
    return (x, y)

def t_prime(x, y, z=None):
    x = x - 360
    return (x, y)

featuers = []
features_joined = []
for sect in whp_sections:
    section = whp_sections[sect]
    if section.length > 360:
        feature = geojson.Feature(geometry=section, properties={"WHP_Section": sect})
        features_joined.append(feature)
        with open(f"woce_lines/{sect}_joined.geojson", 'w') as f:
            f.write(geojson.dumps(feature, indent=2))
        shifted = transform(t, section)
        split_section = split(shifted, antimeridian)
        section = MultiLineString([split_section[0], transform(t_prime, split_section[1])])
    feature = geojson.Feature(geometry=section, properties={"WHP_Section": sect})
    with open(f"woce_lines/{sect}.geojson", 'w') as f:
            f.write(geojson.dumps(feature, indent=2))
    featuers.append(feature)
with open("woce_lines.geojson", 'w') as f:
    collection = geojson.FeatureCollection(featuers)
    f.write(geojson.dumps(collection, indent=2))

