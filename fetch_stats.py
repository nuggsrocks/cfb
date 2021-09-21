import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import json
from globals import teams_list

roster_url = 'https://www.espn.com/college-football/team/roster/_/id/'

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'

stats_url = 'https://www.espn.com/college-football/team/schedule/_/id/'


def scrape_roster(team_id):
    roster_res = requests.get(roster_url + team_id)

    roster_dfs = pd.read_html(roster_res.text)

    roster_df = roster_dfs[0].append(roster_dfs[1], ignore_index=True).append(
        roster_dfs[2], ignore_index=True
    )

    roster_df = roster_df.drop(columns=['Unnamed: 0'])

    roster_dict = roster_df.to_dict()

    col_labels = {
        'Name': 'name',
        'POS': 'pos',
        'HT': 'height',
        'WT': 'weight',
        'Class': 'class',
        'Birthplace': 'birthplace'
    }

    new_dict = {}

    for key in roster_dict:
        new_dict[col_labels[key]] = roster_dict[key]

    new_dict['number'] = {}

    for index, value in new_dict['name'].items():
        try:
            number_index = re.search('[0-9]{1,2}', value).span()[0]
        except AttributeError:
            new_dict['number'][index] = None
            continue

        new_dict['number'][index] = value[number_index:]
        new_dict['name'][index] = value[:number_index]

    for index, value in new_dict['height'].items():
        split_height = value.split('\'')

        feet = split_height[0]

        try:
            feet = int(feet)
        except IndexError:
            new_dict['height'][index] = None
            continue
        except ValueError:
            new_dict['height'][index] = None
            continue

        inches = split_height[1].replace('"', '')

        inches = int(inches) / 12

        new_dict['height'][index] = feet + inches

    for index, value in new_dict['weight'].items():
        new_dict['weight'][index] = value.replace(' lbs', '')

    return new_dict


def scrape_schedule(team_id):
    schedule_res = requests.get(schedule_url + team_id)

    schedule_df = pd.read_html(schedule_res.text, header=1)[0]

    schedule_dict = schedule_df.to_dict()

    col_labels = {
        'DATE': 'date',
        'OPPONENT': 'opponent',
        'RESULT': 'result',
        'W-L (CONF)': 'win_loss'
    }

    new_dict = {}

    for key in schedule_dict:
        try:
            new_dict[col_labels[key]] = schedule_dict[key]
        except KeyError:
            pass

    cutoff_index = None

    for key, value in new_dict['date'].items():
        if value == 'DATE':
            cutoff_index = key

    for index in range(cutoff_index, len(new_dict['date'])):
        for key in new_dict:
            del new_dict[key][index]

    return new_dict


def scrape_stats(team):
    r = requests.get(
        stats_url + team['id']
    )

    soup = BeautifulSoup(r.text, 'html.parser')

    schedule_table = soup.find_all('table')[0]

    game_links = []

    for tag in schedule_table.find_all('a'):
        if re.search('game', tag['href']):
            game_links.append(tag['href'])

    team_games = []

    for link in game_links:
        r = requests.get(
            link.replace('game/_/gameId/', 'matchup?gameId=')
        )

        try:
            boxscore_df = pd.read_html(r.text, attrs={'id': 'linescore'})[0]
        except ValueError:
            continue

        team_index = boxscore_df.loc[
            lambda x: x['Unnamed: 0'] == team['code']
        ].index[0]

        stat_df = pd.read_html(r.text, match='Matchup')[0]

        stat_df = stat_df.rename(columns={
            'Unnamed: 1': 'off' if team_index == 0 else 'def',
            'Unnamed: 2': 'off' if team_index == 1 else 'def'
        })

        col_labels = {
            '1st Downs': '1st_downs',
            '3rd down efficiency': '3rd_down_eff',
            '4th down efficiency': '4th_down_eff',
            'Total Yards': 'total_yards',
            'Passing': 'pass_yards',
            'Comp-Att': 'pass_eff',
            'Yards per pass': 'pass_ypa',
            'Interceptions thrown': 'ints',
            'Rushing': 'rush_yards',
            'Rushing Attempts': 'rush_att',
            'Yards per rush': 'rush_ypa',
            'Penalties': 'penalties',
            'Turnovers': 'tos',
            'Fumbles lost': 'fumbles_lost',
            'Possession': 'time_of_possession'
        }

        stat_df['Matchup'] = stat_df['Matchup'].apply(
            lambda x: col_labels[x] if col_labels[x] else x)

        stats_dict = stat_df.to_dict(orient='dict')

        new_dict = {
            'off': {},
            'def': {}
        }

        for index in range(len(stats_dict['Matchup'])):
            category = stats_dict['Matchup'][index]

            for key in new_dict:
                value = stats_dict[key][index]
                if category == '3rd_down_eff' or category == '4th_down_eff':
                    values = value.split('-')
                    new_dict[key][category.replace('_eff', 's')] = values[0]
                    new_dict[key][category.replace('_eff', '_att')] = values[1]
                elif category == 'pass_eff':
                    values = value.split('-')
                    new_dict[key][category.replace('_eff', '_cmp')] = values[0]
                    new_dict[key][category.replace('_eff', '_att')] = values[1]
                elif category == 'penalties':
                    values = value.split('-')
                    new_dict[key]['penalties'] = values[0]
                    new_dict[key]['penalty_yards'] = values[1]
                else:
                    new_dict[key][category] = value

        team_games.append(new_dict)

    return team_games


stats = {}
schedule = {}
roster = {}

for team in teams_list:
    # team_roster = scrape_roster(team['id'])
    #
    # roster[team['id']] = team_roster
    #
    # team_schedule = scrape_schedule(team['id'])
    #
    # schedule[team['id']] = team_schedule

    team_stats = scrape_stats(team)

    stats[team['id']] = team_stats

try:
    os.mkdir('data')
except FileExistsError:
    pass


def write_file(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data))
        f.close()


# write_file('data/schedule.json', schedule)
# write_file('data/roster.json', roster)
write_file('data/stats.json', stats)
