import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import warnings
from pandas.core.common import SettingWithCopyWarning


# ignore the copy warnings
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

def get_data(seasons: list, team: str):
    
    df = merge_seasons(seasons, team)
    manager_df = process_manager_history()
    df['manager'] = df['Date'].apply(manager_col,manager_df = manager_df)
    df.reset_index(inplace=True,drop=True)
    
    return df


def merge_seasons(seasons: list, team: str):
    data = pd.DataFrame(columns=['Date','Match','Result','Score','Competition'])
    for season in seasons:
        df = get_season_results(season, team)
        data = pd.concat([data, df])
    
    return data 
    

def get_season_results(season: int, team: str):
# URL of the webpage to scrape
    url = "https://www.11v11.com/teams/" + team + "/tab/matches/season/" + str(season)
    # Set headers to mimic a browser request
    agent = os.environ.get('agent')
    
    headers = {
        "User-Agent": agent
        }

    # Send a GET request to the webpage
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check if the request was successful
    

    # Parse the webpage content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table in the webpage
    table = soup.find('table')

    # Extract headers
    headers = [header.text.strip() for header in table.find_all('th')]

    # Extract rows
    rows = []
    for row in table.find_all('tr'):
        columns = row.find_all('td')
        if columns:  # skip headers
            rows.append([column.text.strip() for column in columns])

    # Create a DataFrame
    df = pd.DataFrame(rows, columns=headers)

    df['Date'] = pd.to_datetime(df['Date'])

    return df


def manager_col(match_date: datetime, manager_df: pd.DataFrame):        
    for i, manager in enumerate(manager_df['manager']):
        if manager_df['start_date'].iloc[i] <= match_date <= manager_df['end_date'].iloc[i]:
            return manager


def process_manager_history():
    manager_df = pd.read_csv('manager_history.csv')
    manager_df['start_date'] = pd.to_datetime(manager_df['start_date'],format="%d %b, %Y")
    
    for i, col in enumerate(manager_df['end_date']):
        if col == 'Present':
            manager_df['end_date'].iloc[i] = datetime.today()
        else:
            manager_df['end_date'].iloc[i] = pd.to_datetime(manager_df['end_date'].iloc[i])
    
    return manager_df


if __name__ == "__main__":
    seasons = [i for i in range(1987,2025)]
    raw_data = get_data(seasons,"manchester-united")
    pep_df = get_data([2017,2018],'manchester-city')
    pep_df['manager'] = 'Pep Guardiola'
    klopp_df = get_data([2016,2017],'liverpool')
    klopp_df['manager'] = 'Jurgen Klopp'
    arteta_df = get_data([2020,2021],'arsenal')
    arteta_df['manager'] = 'Mikel Arteta'