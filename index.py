import requests
import os
import re
import pandas as pd

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'

stats_url = 'https://www.espn.com/college-football/team/stats/_/id/'

roster_url = 'https://www.espn.com/college-football/team/roster/_/id/'


teams_list = [
    {'name': 'Illinois', 'nickname': 'Fighting Illini', 'id': '356'},
    {'name': 'Indiana', 'nickname': 'Hoosiers', 'id': '84'},
    {'name': 'Iowa', 'nickname': 'Hawkeyes', 'id': '2294'},
    {'name': 'Maryland', 'nickname': 'Terrapins', 'id': '120'},
    {'name': 'Michigan State', 'nickname': 'Spartans', 'id': '127'},
    {'name': 'Michigan', 'nickname': 'Wolverines', 'id': '130'},
    {'name': 'Minnesota', 'nickname': 'Golden Gophers', 'id': '135'},
    {'name': 'Nebraska', 'nickname': 'Cornhuskers', 'id': '158'},
    {'name': 'Northwestern', 'nickname': 'Wildcats', 'id': '77'},
    {'name': 'Ohio State', 'nickname': 'Buckeyes', 'id': '194'},
    {'name': 'Penn State', 'nickname': 'Nittany Lions', 'id': '213'},
    {'name': 'Purdue', 'nickname': 'Boilermakers', 'id': '2509'},
    {'name': 'Rutgers', 'nickname': 'Scarlet Knights', 'id': '164'},
    {'name': 'Wisconsin', 'nickname': 'Badgers', 'id': '275'}
]

try:
    os.mkdir('data')
except FileExistsError:
    pass


def scrape_schedule(team):
    schedule_res = requests.get(schedule_url + team['id'])

    schedule_df = pd.read_html(schedule_res.text, header=1)[0]

    schedule_df = schedule_df.drop(columns=['HI PASS', 'HI RUSH', 'HI REC', 'Unnamed: 7'])

    cutoff_index = schedule_df.loc[schedule_df['DATE'] == 'DATE'].index[0]

    future_games_index = pd.RangeIndex(start=cutoff_index, stop=schedule_df.index[-1] + 1)

    schedule_df = schedule_df.drop(index=future_games_index)

    return schedule_df


def scrape_roster(team):
    roster_res = requests.get(roster_url + team['id'])

    roster_dfs = pd.read_html(roster_res.text)

    roster_df = roster_dfs[0].append(roster_dfs[1], ignore_index=True).append(roster_dfs[2], ignore_index=True)

    roster_df = roster_df.drop(columns=['Unnamed: 0'])

    roster_df[['Name', 'Number']] = roster_df['Name'].apply(lambda x: pd.Series([str(x)[:re.search('[0-9]{1,2}', str(x)).span()[0]], re.search('[0-9]{1,2}', str(x)).group()]))

    return roster_df


for team in teams_list:
    dirname = 'data/' + team['name'].lower().replace(' ', '_')
    try:
        os.mkdir(dirname)
    except FileExistsError:
        pass

    scrape_schedule(team)
    scrape_roster(team)

    break
