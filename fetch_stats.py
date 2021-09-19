import requests
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from globals import teams_list

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'

stats_url = 'https://www.espn.com/college-football/team/schedule/_/id/'

roster_url = 'https://www.espn.com/college-football/team/roster/_/id/'


def scrape_schedule(team_id):
    schedule_res = requests.get(schedule_url + team_id)

    schedule_df = pd.read_html(schedule_res.text, header=1)[0]

    schedule_df = schedule_df.drop(
        columns=['HI PASS', 'HI RUSH', 'HI REC', 'Unnamed: 7']
    )

    cutoff_index = schedule_df.loc[schedule_df['DATE'] == 'DATE'].index[0]

    future_games_index = pd.RangeIndex(start=cutoff_index,
                                       stop=schedule_df.index[-1] + 1)

    schedule_df = schedule_df.drop(index=future_games_index)

    schedule_df = schedule_df.rename(columns={
        'DATE': 'date',
        'OPPONENT': 'opponent',
        'RESULT': 'result',
        'W-L (CONF)': 'win_loss'
    })

    schedule_df['team_id'] = team_id

    return schedule_df


def scrape_roster(team_id):
    roster_res = requests.get(roster_url + team_id)

    roster_dfs = pd.read_html(roster_res.text)

    roster_df = roster_dfs[0].append(roster_dfs[1], ignore_index=True).append(
        roster_dfs[2], ignore_index=True)

    roster_df = roster_df.drop(columns=['Unnamed: 0'])

    def split_name_and_number(x):
        x = str(x)

        try:
            number_index = re.search('[0-9]{1,2}', x).span()[0]
        except AttributeError:
            return pd.Series([x, None])

        name = x[0:number_index]
        number = x[number_index:]

        return pd.Series([name, number])

    roster_df[['Name', 'Number']] = roster_df['Name'].apply(
        split_name_and_number)

    def convert_height(x):
        y = x.split('\'')

        feet = y[0]

        try:
            feet = int(feet)
        except IndexError:
            return None
        except ValueError:
            return None

        inches = y[1].replace('"', '')

        inches = int(inches) / 12

        return feet + inches

    roster_df['HT'] = roster_df['HT'].apply(convert_height)

    roster_df['WT'] = roster_df['WT'].apply(lambda x: x.replace(' lbs', ''))

    roster_df = roster_df.rename(columns={
        'Name': 'name',
        'POS': 'position',
        'HT': 'height',
        'WT': 'weight',
        'Class': 'class',
        'Birthplace': 'birthplace',
        'Number': 'number'
    })

    roster_df['team_id'] = team_id

    return roster_df


game_index = 0


def scrape_stats(team):
    global game_index

    r = requests.get(
        stats_url + team['id']
    )

    soup = BeautifulSoup(r.text, 'html.parser')

    schedule_table = soup.find_all('table')[0]

    game_links = []

    for tag in schedule_table.find_all('a'):
        if re.search('game', tag['href']):
            game_links.append(tag['href'])

    team_stats = pd.DataFrame()

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

        stat_df['Matchup'] = stat_df['Matchup'].apply(lambda x: col_labels[x] if col_labels[x] else x)

        stat_df = stat_df.drop_duplicates(subset=['Matchup'])

        stat_df = stat_df.set_index(['Matchup'])

        stat_df = stat_df.T

        stat_df['game_id'] = game_index

        stat_df = stat_df.reset_index()

        stat_df = stat_df.set_index(['game_id', 'index'])

        team_stats = team_stats.append(stat_df)

        game_index += 1

    team_stats['team_id'] = team['id']

    return team_stats


stats_df = pd.DataFrame()
schedule_df = pd.DataFrame()
roster_df = pd.DataFrame()

for team in teams_list:
    team_stats = scrape_stats(team)
    team_schedule = scrape_schedule(team['id'])
    team_roster = scrape_roster(team['id'])

    stats_df = stats_df.append(team_stats)
    schedule_df = schedule_df.append(team_schedule)
    roster_df = roster_df.append(team_roster)


try:
    os.mkdir('data')
except FileExistsError:
    pass

stats_df.to_json('data/stats.json')

schedule_df = schedule_df.reset_index(drop=True)
schedule_df.to_json('data/schedule.json')

roster_df = roster_df.reset_index(drop=True)
roster_df.to_json('data/roster.json')
