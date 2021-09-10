import requests
import os
import re
import pandas as pd

schedule_url = 'https://www.espn.com/college-football/team/schedule/_/id/'

stats_url = 'https://www.espn.com/college-football/team/stats/_/type/team/id/'

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


def scrape_schedule(team_id):
    schedule_res = requests.get(schedule_url + team_id)

    schedule_df = pd.read_html(schedule_res.text, header=1)[0]

    schedule_df = schedule_df.drop(
        columns=['HI PASS', 'HI RUSH', 'HI REC', 'Unnamed: 7'])

    cutoff_index = schedule_df.loc[schedule_df['DATE'] == 'DATE'].index[0]

    future_games_index = pd.RangeIndex(start=cutoff_index,
                                       stop=schedule_df.index[-1] + 1)

    schedule_df = schedule_df.drop(index=future_games_index)

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

    return roster_df


def scrape_stats(team_id, team_name):
    stats_res = requests.get(stats_url + team_id)

    stats_dfs = pd.read_html(stats_res.text)

    label_series = pd.Series(stats_dfs[0]['Scoring'])

    label_series = label_series.drop(index=[3, 12, 20, 26, 30, 37, 42, 45, 47])

    label_series = label_series.reset_index(drop=True)

    stats_series = pd.Series(stats_dfs[1][team_name])

    stats_df = pd.DataFrame(data=stats_series)

    stats_df = stats_df.set_index(keys=label_series)

    return stats_df.rename(mapper={
        'Total Points Per Game': 'PPG',
        'Total Points': 'Points',
        'Total Touchdowns': 'Touchdowns',
        'Total 1st downs': '1st Downs',
        '1st downs by penalty': 'Penalty 1st Downs',
        '3rd down efficiency': '3rd Downs',
        '3rd down %': '3rd Down Efficiency',
        '4th down efficiency': '4th Downs',
        '4th down %': '4th Down Efficiency',
        'Net Passing Yards': 'Passing Yards',
        'Net Passing Yards Per Game': 'Passing YPG',
    })


def save_stats():
    for team in teams_list:
        team_stats = scrape_stats(team['id'], team['name'])
        team_schedule = scrape_schedule(team['id'])
        team_roster = scrape_roster(team['id'])

        try:
            os.mkdir('data')
        except FileExistsError:
            pass

        dirname = 'data/' + team['name'].lower().replace(' ', '_')
        try:
            os.mkdir(dirname)
        except FileExistsError:
            pass

        team_stats.to_json(dirname + '/stats.json')
        team_schedule.to_json(dirname + '/schedule.json', orient='records')
        team_roster.to_json(dirname + '/roster.json', orient='records')


save_stats()
