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


def get_team(name):
    team_id = get_team_id(name)
    return {
        'stats': stats.loc[team_id],
        'roster': roster.loc[roster['team_id'] == team_id],
        'schedule': schedule.loc[schedule['team_id'] == team_id]
    }


michigan = get_team('Michigan')


