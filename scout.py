# scout.py
# 
# Automated scouting using tracking data

# read from files
#  /game
#     areas.csv (label, filename, alliance)
#     <files>
# ELO
# bot-scout
# read motionworks
#  - make polygon from robot
#  - hit test dataset by time val


# things I want to do:
# - identify the field zones
# - pull data
# - track amount of time spent in zones
# - time between zones or locations
# - associate with scoring?
# - asesss offense / defense
# - proximity to other robots
# - plus minus
# - offense/defense

# curl -X 'GET'  'https://www.thebluealliance.com/api/v3/match/2023wasno_sf13m1/zebra_motionworks?X-TBA-Auth-Key=<stick your API key here>'

import json
import requests
import numpy as np
import pandas as pd
import geopandas as gp
import shapely as sh
import matplotlib.pyplot as plt
import base64

frc_user = 'natebrix'
frc_key = '48c572cc-fa96-45e1-87df-74656ea676ad' # todo file
key_first = b'natebrix:48c572cc-fa96-45e1-87df-74656ea676ad' # todo file
def frc_auth_key():
    return base64.b64encode(key_first)

keys = { \
         'tba': 'CTr4JltR51QmvBuOCEl3gSSPIjsI9TaS4uHOf52Fi0FPZb9jbHV4zcjoaSMyrKlm', \
         'frc' : frc_auth_key()
         }

url_tba = 'https://www.thebluealliance.com/api/v3'
team_bhs = 'frc4915'
frc_events_bhs = ['WASNO']
tba_events_bhs = ['2023wasno']

match = '2023wasno_sf13m1'

# /match/{match_key}/simple (teams and scores)

# https://frc-api-docs.firstinspires.org/#58da7b76-4b47-4ee3-903d-1571897e0a09
# https://frc-events.firstinspires.org/services/API ### AUTH SIGNUP
# Your Username:natebrix
# Your Authorization Token:48c572cc-fa96-45e1-87df-74656ea676ad

################################################################################

class FrcApi:
    def __init__(self, user, key):
        self.user = user
        self.key = key
        self.base_url = 'https://frc-api.firstinspires.org/v3.0'

    def header(self):
        t = f'{self.user}:{self.key}'
        b = t.encode('ascii')
        v = base64.b64encode(b).decode()
        return {'Authorization': f'Basic {v}'}

    def get_json(self, u):
        r = requests.get(url=u, headers=self.header())
        return json.loads(r.text)

    def url_event_scores(self, year, event, level):
        return f'{self.base_url}/{year}/scores/{event}/{level}'
    
    def get_event_scores(self, year, event, level):
        u = self.url_event_scores(year, event, level)
        return self.get_json(u)

    def url_event_matches(self, year, event):
        return f'{self.base_url}/{year}/matches/{event}'

    def get_event_matches(self, year, event):
        u = self.url_event_matches(year, event)
        return self.get_json(u)

    
################################################################################

class BlueAllianceApi:
    def __init__(self, key):
        self.key = key
        
    def url_zebra_motionworks(self, match):
        return f"{url_tba}/match/{match}/zebra_motionworks?X-TBA-Auth-Key={self.key}"

    def url_team_event_matches(self, event, team):
        return f"{url_tba}/team/{team}/event/{event}/matches?X-TBA-Auth-Key={self.key}"

    def url_event_matches(self, event):
        return f"{url_tba}/event/{event}/matches?X-TBA-Auth-Key={self.key}"

    def get_json(self, u):
        r = requests.get(url=u)
        return json.loads(r.text)
    
    def get_team_event_matches(self, event, team):
        u = self.url_team_event_matches(event, team)
        return self.get_json(u)

    def get_event_matches(self, event):
        u = self.url_event_matches(event)
        return self.get_json(u)

    # z['alliances']['blue'][0]['team_key'] / xs/ys
    # list(zip(z['alliances']['blue'][1]['xs'], z['alliances']['blue'][1]['ys']))
    def get_match_zebra_motionworks(self, match):
        u = self.url_zebra_motionworks(match)
        return self.get_json(u)

    def get_event_zebra_motionworks(self, event):
        em = self.get_event_matches(event)
        match_keys = [m['key'] for m in em]
        print(f'Retrieving {len(match_keys)} motionworks')
        return [{'key':match, 'data':self.get_match_zebra_motionworks(match)} for match in match_keys]

def write_key_value_to_file(items, prefix, path, extension="json"):
    for item in items:
        filename = f'{path}/{prefix}_{item["key"]}.{extension}'
        print(f'Writing: {filename}')
        with open(filename, 'w') as f:
            f.write(json.dumps(item['data']))
    
def teams_alliances(teams, a):
    return [(t, a) for t in teams[a]]
    
def motionworks_teams(mw):
    return teams_alliances(mw['alliances'], 'red') + teams_alliances(mw['alliances'], 'blue')


def bot_distances(md, hit_distance=2.0):
    teams = [c for c in md.columns if c[:3]=='frc']
    tc = [(t1, t2) for t1 in teams for t2 in teams if t1 != t2]
    names = [f'd_{pair[0]}_{pair[1]}' for pair in tc]
    hit = [f'h_{pair[0]}_{pair[1]}' for pair in tc]
    for i, pair in enumerate(tc):
        md[names[i]] = md.apply(lambda r: r[pair[0]].distance(r[pair[1]]), axis=1)
    for i, pair in enumerate(tc):
        md[hit[i]] = (md[names[i]] < hit_distance)
        md[hit[i]] = md[hit[i]].astype(float)
    # todo (hit team, hit opp)

def bot_areas(md, areas, teams):
    #red = [mw['alliances']['red'][0]['team_key']
    for i in areas.index:
        area_alliance = areas.loc[i, 'alliance']
        label = area_alliance
        for (team, a) in teams:
            t = team['team_key']
            if area_alliance != 'field':
                label = 'own' if area_alliance == a else 'opp'
            md[f'h_{t}_{label}_{areas.loc[i, "id"]}'] = md[t].apply(lambda x: int(areas.loc[i, 'geom'].contains(x)))
    # I would also like to have alliance level hit tests, I think?!?

def teammate_map():
    return {} # key is team, value is pair of lists (own, opp)

def motionworks_match(mw):
    teams = motionworks_teams(mw)
    times = mw['times']
    data = [[t] + [sh.Point(team['xs'][i], team['ys'][i]) for (team, a) in teams] for i, t in enumerate(times)]
    return pd.DataFrame(data, columns=['time'] + [t['team_key'] for (t, a) in teams])

def motionworks_match_details(mw, areas):
    md = motionworks_match(mw)
    bot_distances(md)
    teams = motionworks_teams(mw)
    bot_areas(md, areas, teams)
    return md
            
#matches = api.get_team_event_matches(events_bhs[0], team_bhs)
#mw = api.get_match_zebra_motionworks(matches[0]['key'])    
#xy = list(zip(mw['alliances']['blue'][1]['xs'], mw['alliances']['blue'][1]['ys']))

################################################################################


# zones
# blue / red (halves)
# community
#    18' high (549)
#    11'3/8" short part (336)
#    16'1 1/4" long part (491)
# field
#    26 3 1/2 high (802)
#    54 3 1/4 long (1654)
# alliance area (for people)
#    20' high (609)
#    9' 10 1/4" wide

# let (left, bottom) = (0, 0)

#A CHARGE STATION is an 8 ft. 1¼ in. (~247 cm) wide, 6 ft. 4⅛ in. (~193 cm) deep structure that is
#located in each COMMUNITY such that its center is 8 ft. 2⅝ in. (~251 cm) from the far edge of the GRID’S
#tape line and centered in the width of the COMMUNITY. 

#r = requests.get(url = URL, params = PARAMS)

def inches(feet, inch=0):
    return 12 * feet + inch

def feet(feet, inch=0):
    return feet + inch / 12.0

field_w = feet(54, 3.25)
field_h = feet(26, 3.5)
field = sh.geometry.Polygon([sh.Point(0, 0), sh.Point(field_w, 0), sh.Point(field_w, field_h), sh.Point(0, field_h), sh.Point(0, 0)])


center = field_w / 2.0
red_half = sh.geometry.Polygon([sh.Point(0, 0), sh.Point(center, 0), sh.Point(center, field_h), sh.Point(0, field_h), sh.Point(0, 0)])
blue_half = sh.geometry.Polygon([sh.Point(center, 0), sh.Point(field_w, 0), sh.Point(field_w, field_h), sh.Point(center, field_h), sh.Point(center, 0)])

def flip_horizontal(shape):
    return sh.geometry.Polygon([sh.Point(field_w - p[0], p[1]) for p in shape.boundary.coords])

# todo all of this in files
comm_w_min = feet(11, 3.0/8) 
comm_w_max = feet(16, 1.25) 
comm_h = feet(18) 
comm_h_top = feet(4) # todo
comm_h_mid = comm_h - comm_h_top
red_comm = sh.geometry.Polygon([sh.Point(0, 0), sh.Point(0, comm_h), sh.Point(comm_w_min, comm_h), \
                      sh.Point(comm_w_min, comm_h_mid), sh.Point(comm_w_max, comm_h_mid),\
                      sh.Point(comm_w_max, 0), sh.Point(0, 0)])
blue_comm = flip_horizontal(red_comm)



# loading zone
#    leading edge is 61.36 from center of field
#    leading edge is 50.50 high
#    8'3" high (252 cm)
#    11'1/4" short part (335)
#    22'1/4" long part (671)

loading_w_max = feet(22, inch=.25) 
loading_w_min = feet(11, inch=.25)
loading_h_top = feet(0, inch=50.5)
loading_h = feet(8, inch=3)

red_loading = sh.geometry.Polygon([sh.Point(field_w, field_h), \
                         sh.Point(field_w - loading_w_max, field_h), \
                         sh.Point(field_w - loading_w_max, field_h - loading_h_top), \
                         sh.Point(field_w - loading_w_min, field_h - loading_h_top), \
                         sh.Point(field_w - loading_w_min, field_h - loading_h), \
                         sh.Point(field_w, field_h - loading_h), \
                         sh.Point(field_w, field_h)])
blue_loading = flip_horizontal(red_loading)

# charging pad
#    6'4 1/8" wide
#    8' long
#    4' top
#    1'2 1/16" ramp width
charge_w = feet(6, 4.125)
charge_h = feet(8)
charge_x_offset = comm_w_max - charge_w
charge_y_offset = comm_h_mid - charge_h

red_charge = sh.geometry.Polygon([sh.Point(charge_x_offset, charge_y_offset), \
                        sh.Point(charge_x_offset + charge_w, charge_y_offset), \
                        sh.Point(charge_x_offset + charge_w, charge_y_offset + charge_h), \
                        sh.Point(charge_x_offset, charge_y_offset + charge_h), \
                        sh.Point(charge_x_offset, charge_y_offset)])
blue_charge = flip_horizontal(red_charge)

def make_polygon(pts):
    return sh.geometry.Polygon([[p.x, p.y] for p in pts])

# def make_blue_series():
# p = gpd.GeoSeries(blue_areas)

#####

tba = BlueAllianceApi(keys['tba'])
frc = FrcApi(frc_user, frc_key) 

area_list = [    
          ['all', field, 'field'],
          ['half', blue_half, 'blue'],
          ['comm', blue_comm, 'blue'],
          ['loading', blue_loading, 'blue'],
          ['charge', blue_charge, 'blue'],
          ['half', red_half, 'red'],
          ['comm', red_comm, 'red'],
          ['loading', red_loading, 'red'],
          ['charge', red_charge, 'red'],
    ]
areas = gp.GeoDataFrame(area_list, columns=['id', 'geom', 'alliance'], geometry='geom')
            

# need outlier detection

def plot_areas(areas):
    areas.plot()
    plot.show()

def single_match_data(m):
    alliances = ['red', 'blue']
    v = {}
    keys = ['event_key', 'key', 'match_number', 'winning_alliance', 'comp_level']
    for key in keys:
        v |= { f'{key}': m[key] for key in keys }
    for alliance in alliances:
        v |= { f'{alliance}_{key}': value for key, value in m['alliances'][alliance].items() }
        v |= { f'{alliance}_{key}': value for key, value in m['score_breakdown'][alliance].items() }
    return v

def get_all_match_data(em):
    ds = [single_match_data(m) for m in em]
    return pd.DataFrame(ds)
    
# match details: (rows are times; dataset per match)
#   area x bot (contains)
#   bot x bot (intersect / distance)
    
# match summary: (rows are matches)
# per alliance
#    total score
#    score breakdown [ in event matches ]
#    mean velocity
#    time in each area
# per bot:
#    percent of time in each area
#    collisions (own, opp)

# bot-match (rows are matches)
#   match results as rows [from match]

# bot (rows are bots) # (this is roll up from bot-match results)
#  name, school, etc
#  average time in area
#  skill ratings
