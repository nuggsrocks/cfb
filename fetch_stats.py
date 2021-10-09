import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import json
from globals import teams_list

roster_url = 'https://www.espn.com/college-football/team/roster/_/id/'

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'


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


def scrape_plays(id):
    base_url = "http://cdn.espn.com/core/college-football/playbyplay"

    params = {
        'gameId': id,
        'xhr': 1,
        'render': "false",
        'userab': 18
    }

    r = requests.get(base_url, params=params)

    game_json = json.loads(r.content)['gamepackageJSON']

    drives = game_json['drives']['previous']

    plays = []

    for drive in drives:
        plays.extend(drive['plays'])

    return plays


def scrape_stats(team):
    r = requests.get(
        schedule_url + team['id']
    )

    soup = BeautifulSoup(r.text, 'html.parser')

    schedule_table = soup.find_all('table')[0]

    game_links = []

    for tag in schedule_table.find_all('a'):
        if re.search('game', tag['href']):
            game_links.append(tag['href'])

    team_games = {}

    for i in range(0, len(game_links)):
        link = game_links[i]
        game_id = re.search('gameId/[0-9]+', link).group().replace('gameId/',
                                                                   '')
        try:
            plays = scrape_plays(game_id)
        except KeyError:
            continue

        team_games[game_id] = plays

    return team_games


def scrape_team_data(team):
    team_roster = scrape_roster(team['id'])

    team_schedule = scrape_schedule(team['id'])

    team_stats = scrape_stats(team)

    return team_roster, team_schedule, team_stats


def scrape_all_data():
    roster = {}
    schedule = {}
    stats = {}

    for i in range(0, len(teams_list)):
        team = teams_list[i]

        print('Scraping team {} data...'.format(i + 1))

        team_roster, team_schedule, team_stats = scrape_team_data(team)

        roster[team['id']] = team_roster
        schedule[team['id']] = team_schedule
        stats[team['id']] = team_stats

    return roster, schedule, stats


try:
    os.mkdir('data')
except FileExistsError:
    pass


def write_file(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data))
        f.close()


if __name__ == '__main__':
    roster, schedule, stats = scrape_all_data()

    print('Writing files...')
    write_file('data/schedule.json', schedule)
    write_file('data/roster.json', roster)
    write_file('data/stats.json', stats)
