from multiprocessing import Pool

import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import json
from globals import teams_list

roster_url = 'https://www.espn.com/college-football/team/roster/_/id/'

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'


def scrape_roster(team):
    roster_res = requests.get(roster_url + team['id'])

    roster_dfs = pd.read_html(roster_res.text)

    roster_df = roster_dfs[0].append(roster_dfs[1], ignore_index=True).append(
        roster_dfs[2], ignore_index=True
    )

    roster_df = roster_df.drop(columns=['Unnamed: 0'])

    col_labels = {
        'Name': 'name',
        'POS': 'pos',
        'HT': 'height',
        'WT': 'weight',
        'Class': 'class',
        'Birthplace': 'birthplace'
    }

    roster_df = roster_df.rename(columns=col_labels)

    def split_name_num(str):
        match = re.search('[0-9]+', str)
        if match is None:
            return pd.Series([str, None])

        return pd.Series([str[0:match.span()[0]], str[match.span()[0]:]])

    roster_df[['name', 'number']] = roster_df['name'].apply(split_name_num)

    def format_height(str):
        split_height = str.split('\'')

        try:
            feet = int(split_height[0])
        except ValueError:
            return None

        inches = int(split_height[1].replace('"', ''))

        return feet + (inches / 12)

    roster_df['height'] = roster_df['height'].apply(format_height)

    roster_df['weight'] = roster_df['weight'].str.replace(' lbs', '')

    roster_df['team_id'] = team['id']

    return roster_df


def scrape_schedule(team):
    schedule_res = requests.get(schedule_url + team['id'])

    schedule_df = pd.read_html(schedule_res.text, header=1)[0]

    schedule_df = schedule_df.drop(columns=['HI PASS', 'HI RUSH', 'HI REC', 'Unnamed: 7'])

    col_labels = {
        'DATE': 'date',
        'OPPONENT': 'opponent',
        'RESULT': 'result',
        'W-L (CONF)': 'win_loss'
    }

    schedule_df = schedule_df.rename(columns=col_labels)

    cutoff = pd.RangeIndex(start=schedule_df[schedule_df['date'] == 'DATE'].index[0], stop=len(schedule_df))

    schedule_df = schedule_df.drop(index=cutoff)

    schedule_df['team_id'] = team['id']

    return schedule_df


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

    team_df = pd.DataFrame()

    for i in range(0, len(game_links)):
        link = game_links[i]
        game_id = re.search('gameId/[0-9]+', link).group().replace('gameId/',
                                                                   '')
        try:
            plays = scrape_plays(game_id)
        except KeyError:
            continue

        game_df = pd.DataFrame()

        for play in plays:
            try:
                match = re.search('End of|Timeout', play['type']['text'])
            except KeyError:
                continue

            if match is not None:
                continue

            play['period'] = [play['period']['number']]
            play['home_score'] = [play['homeScore']]
            play['clock'] = [play['clock']['displayValue']]
            play['type'] = [play['type']['text']]
            play['stat_yards'] = [play['statYardage']]
            play['away_score'] = [play['awayScore']]
            play['start_yard_line'] = [play['start']['yardLine']]
            play['down'] = [play['start']['down']]
            play['distance'] = [play['start']['distance']]
            play['team_id'] = [play['start']['team']['id']]
            play['end_yard_line'] = [play['end']['yardLine']]

            keys_to_delete = [
                'scoringType',
                'homeScore',
                'statYardage',
                'awayScore',
                'wallclock',
                'modified',
                'start',
                'id',
                'end',
                'sequenceNumber',
                'scoringPlay',
                'priority',
                'text',
                'mediaId'
            ]

            for key in keys_to_delete:
                try:
                    del play[key]
                except KeyError:
                    continue

            game_df = game_df.append(pd.DataFrame(play), ignore_index=True)

        game_df['game_id'] = game_id

        team_df = team_df.append(game_df, ignore_index=True)

    return team_df


def scrape_team_data(team):
    print('Scraping data for {}...'.format(team['name']))
    team_roster = scrape_roster(team)

    team_schedule = scrape_schedule(team)

    team_stats = scrape_stats(team)

    return team_roster, team_schedule, team_stats


try:
    os.mkdir('data')
except FileExistsError:
    pass


def write_file(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data))
        f.close()


if __name__ == '__main__':
    with Pool(14) as p:
        dfs = p.map(scrape_team_data, teams_list)

    roster_df = pd.DataFrame()
    schedule_df = pd.DataFrame()
    stats_df = pd.DataFrame()

    for team in dfs:
        roster_df = roster_df.append(team[0], ignore_index=True)
        schedule_df = schedule_df.append(team[1], ignore_index=True)
        stats_df = stats_df.append(team[2], ignore_index=True)

    print('Writing files...')
    write_file('data/roster.json', roster_df.to_json())
    write_file('data/schedule.json', schedule_df.to_json())
    write_file('data/stats.json', stats_df.to_json())

    print('Done!')
