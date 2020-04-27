from collections import defaultdict
from winreg import *
import click
import cutie

# Utils module for the downloader

def get_download_path(): 
    """
    The function will use winreg module to get the user Download folder path
    :return: path to the Download folder (str)
    """
    with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
        download_path = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
    return download_path


def get_one_result(downloader, tv_show):
    """
    The function will get a spesific result from the search query
    :param tv_show: the name of the tv show (str)
    :return: tv_name, base_url (tupple)
    """
    search_results = downloader.search(tv_show)
    if len(search_results) == 1: # Case that there was only one result
        return search_results[0] 
    click.echo('Select TV show to download')     
    index = cutie.select([str(tv) for tv in search_results] + ['Exit'])
    if index == len(search_results): #if user wants to exit
        exit()
    return search_results[index]

def parse_seasson_input(seasons):
    """
    The function will parse the season input from the user
    :param seasons: the text to parse (following format 1,2,3,5[3], 6[4:2] - str)
    :return: dict with season number as keys and episodes as values - no episodes means download every episode (collections.defaultdict - keys integers, values sets )
    """
    if not seasons:
        return None
    res = defaultdict(lambda: set())
    for season in seasons.split(','):
        first, second = season.find('['), season.find(']')
        if first != -1 and second != -1:
            episodes = [int(episode) for episode in season[first + 1: second].split(':')]
            res[int(season[:first])].update(set(range(episodes[0],episodes[1])) if len(episodes) != 1 else set(episodes)) # In case that input was like 1:2 adding range ofepisodes, else adding the spesific episode
        else:
            res[int(season)].update(set())
    return res