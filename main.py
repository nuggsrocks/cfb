import re
import time
from multiprocessing import Pool, Process
import pandas as pd

import json

from globals import teams_list


def read_file(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


roster_json = read_file('data/roster.json')
schedule_json = read_file('data/schedule.json')
stats_json = read_file('data/stats.json')

roster_df = pd.read_json(roster_json)
schedule_df = pd.read_json(schedule_json)
stats_df = pd.read_json(stats_json)


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


# def load_team_stats(team_id):
#     team_df = pd.DataFrame()
#     for game_id in stats[team_id]:
#         plays = stats[team_id][game_id]
#
#         plays_to_delete = []
#
#         for play in plays:
#             try:
#                 play['type'] = play['type']['text']
#             except KeyError:
#                 plays_to_delete.append(play)
#                 continue
#
#             if re.search('End of', play['type']) is not None:
#                 plays_to_delete.append(play)
#
#         for play in plays_to_delete:
#             plays.remove(play)
#
#         plays_df = pd.DataFrame()
#
#         for play in plays:
#             play['period'] = play['period']['number']
#             play['start_yard_line'] = play['start']['yardLine']
#             play['end_yard_line'] = play['end']['yardLine']
#             if play['type'] == 'Kickoff':
#                 play['down'] = 'K'
#             else:
#                 play['down'] = play['start']['down']
#
#             play['distance'] = play['start']['distance']
#             play['game_clock'] = play['clock']['displayValue']
#             play['team_id'] = play['start']['team']['id']
#
#             del play['start']
#             del play['clock']
#             del play['end']
#
#             series = pd.Series(play)
#             series['game_id'] = game_id
#
#             plays_df = plays_df.append(series, ignore_index=True)
#
#         team_df = team_df.append(plays_df, ignore_index=True)
#
#     team_df['team_id'] = team_id
#     return team_df


def inc():
    count = 0
    while True:
        time.sleep(1)
        print(count, end='\r', flush=True)
        count += 1


if __name__ == '__main__':
    print(len(stats_df))
