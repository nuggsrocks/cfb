import pandas as pd

import numpy as np

import matplotlib.pyplot as plt

from sklearn import svm

from sklearn.model_selection import train_test_split

from sklearn.metrics import r2_score

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
opp_df = stats_df.xs('opp', level=1)


class Split:
    def __init__(self, df):
        self.df = df.drop(columns=['team_name'])


class Team:
    def __init__(self, team_name):
        self.df = stats_df.loc[stats_df['team_name'] == team_name]
        self.offense = Split(self.df.xs('team', level=1))
        self.defense = Split(self.df.xs('opp', level=1))


class Teams:
    def __init__(self, df):
        self.df = df

    def get_team(self, item):
        return self.df.loc[self.df['team_name'] == item]

    def rank_by_total(self, split, category):
        return self.df.xs(split, level=1).groupby(['team_name'])[category].sum().sort_values(ascending=False)


teams = Teams(stats_df)

print(teams.rank_by_total('team', 'points'))


def select_category(split, category):
    if split == 'off':
        df = team_df.groupby(['team_name'])
    else:
        df = opp_df.groupby(['team_name'])

    try:
        return df[category]
    except KeyError as exc:
        raise exc


def rank_teams_by_total(split, category):
    series = select_category(split, category)

    return series.sum().sort_values(ascending=False)


def rank_teams_by_avg(split, category):
    series = select_category(split, category)

    return series.mean().sort_values(ascending=False)


def rank_teams_by_median(split, category):
    series = select_category(split, category)

    return series.median().sort_values(ascending=False)


def get_team_total(team_name, split, category):
    series = select_category(split, category)

    return series.sum().loc[team_name]


def get_team_avg(team_name, split, category):
    series = select_category(split, category)

    return series.mean().loc[team_name]
