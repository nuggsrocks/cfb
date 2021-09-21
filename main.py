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
            return team['id']
    return None


roster_df = pd.DataFrame()
schedule_df = pd.DataFrame()
stats_df = pd.DataFrame()

for team_id, team_roster in roster.items():
    team_roster_df = pd.DataFrame(data=team_roster)

    team_roster_df['team_id'] = team_id

    roster_df = roster_df.append(team_roster_df, ignore_index=True)

for team_id, team_schedule in schedule.items():
    team_schedule_df = pd.DataFrame(data=team_schedule)

    team_schedule_df['team_id'] = team_id

    schedule_df = schedule_df.append(team_schedule_df, ignore_index=True)

for team_id, team_stats in stats.items():
    stats_dict = {}
    for game_index in range(len(team_stats)):
        for key in team_stats[game_index]:
            stats_dict[game_index, key] = team_stats[game_index][key]

    team_stats_df = pd.DataFrame(stats_dict)

    team_stats_df = team_stats_df.T

    team_stats_df['team_id'] = team_id

    stats_df = stats_df.append(team_stats_df)


def set_stat_dtype(series):
    try:
        return series.astype('int')
    except ValueError:
        try:
            return series.astype('float')
        except ValueError:
            return series.astype('string')


stats_df = stats_df.apply(set_stat_dtype)

print(stats_df)
