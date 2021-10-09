import re

import pandas as pd

import json

from globals import teams_list


def read_file(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


roster = read_file('data/roster.json')
schedule = read_file('data/schedule.json')
stats = read_file('data/stats.json')


def get_team_id(name):
    for team in teams_list:
        if team['name'] == name:
            return int(team['id'])
    return None


def get_team_name(team_id):
    for team in teams_list:
        if team['id'] == team_id:
            return team['name']
    return None


for team_id in stats:
    team_stats = {'off': [], 'def': []}
    for game_id in stats[team_id]:
        plays = stats[team_id][game_id]

        plays_to_delete = []

        for play in plays:
            try:
                play['type'] = play['type']['text']
            except KeyError:
                plays_to_delete.append(play)
                continue

            if re.search('End of', play['type']) is not None:
                plays_to_delete.append(play)

        for play in plays_to_delete:
            plays.remove(play)

        for play in plays:

            play['period'] = play['period']['number']
            play['start_yard_line'] = play['start']['yardLine']
            play['end_yard_line'] = play['end']['yardLine']

            if play['type'] == 'Kickoff':
                play['down'] = 'K'
            else:
                play['down'] = play['start']['down']

            if play['start']['team']['id'] == team_id:
                team_stats['off'].append(play)
            else:
                team_stats['def'].append(play)

    stats[team_id] = team_stats

print(len(stats))
