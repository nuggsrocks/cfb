import re

import pandas as pd

from globals import teams_list

try:
    stats = pd.read_json('data/stats.json')
    roster = pd.read_json('data/roster.json')
    schedule = pd.read_json('data/schedule.json')
except ValueError as exc:
    raise exc


def get_team_id(name):
    for team in teams_list:
        if team['name'] == name:
            return int(team['id'])
    return None


print(stats)
