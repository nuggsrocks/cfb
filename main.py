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


roster_df = pd.DataFrame()
schedule_df = pd.DataFrame()
stats_df = pd.DataFrame()

for team_id, team_roster in roster.items():
    team_roster_df = pd.DataFrame(data=team_roster)

    team_roster_df['team_name'] = get_team_name(team_id)

    roster_df = roster_df.append(team_roster_df, ignore_index=True)

for team_id, team_schedule in schedule.items():
    team_schedule_df = pd.DataFrame(data=team_schedule)

    team_schedule_df['team_name'] = get_team_name(team_id)

    schedule_df = schedule_df.append(team_schedule_df, ignore_index=True)

for team_id, team_stats in stats.items():
    stats_dict = {}
    for game_index in range(len(team_stats)):
        for key in team_stats[game_index]:
            stats_dict[game_index, key] = team_stats[game_index][key]

    team_stats_df = pd.DataFrame(stats_dict)

    team_stats_df = team_stats_df.T

    team_stats_df['team_name'] = get_team_name(team_id)

    stats_df = stats_df.append(team_stats_df)


def set_stat_dtype(series):
    if series.name == 'time_of_possession':
        def convert_to_seconds(x):
            split = x.split(':')
            minutes = int(split[0])
            seconds = int(split[1])
            return minutes * 60 + seconds
        return series.apply(convert_to_seconds)
    else:
        try:
            return series.astype('int')
        except ValueError:
            try:
                return series.astype('float')
            except ValueError:
                return series.astype('string')


stats_df = stats_df.apply(set_stat_dtype)

team_df = stats_df.xs('team', level=1)


def rank_teams_by_total(category):
    df = team_df.groupby(['team_name'])

    try:
        df = df[category]
    except KeyError as exc:
        raise exc

    return df.sum().sort_values(ascending=False)


def rank_teams_by_avg(category):
    df = team_df.groupby(['team_name'])

    try:
        df = df[category]
    except KeyError as exc:
        raise exc

    return df.mean().sort_values(ascending=False)


print(rank_teams_by_avg('total_yards'))
