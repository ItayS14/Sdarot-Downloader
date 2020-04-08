from downloader import SdarotDownloader, Episode
import click
import cutie
import re
import os
from winreg import *
import concurrent.futures
from collections import defaultdict

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

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--seasons', default=None, help="Seasons to download, divided by comma")
@click.option('--download-path', default=get_download_path(), help='Set the downlaod path, by default download path is set to Download folder')
@click.argument('tv_show')
def download(seasons, download_path, tv_show):
    """This script will download tv shows from sdarot tv website
    TV_SHOW is the name of the tv show to download
    """
    downloader = SdarotDownloader('https://sdarot.world/')
    try:
        tv_name, base_url = get_one_result(downloader, tv_show)
        seasons = parse_seasson_input(seasons)
    except ValueError: #Case that season number was not int
        raise click.BadParameter('Seasons must be a number')   
    except SdarotDownloader.NoResultsFound as e:
        raise click.BadOptionUsage(e)
    else:
        print('Downloading:', tv_name)
        download_path = os.path.join(download_path, tv_name)
        print('Download path:', download_path)
        if not os.path.isdir(download_path):
            os.mkdir(download_path)
        os.chdir(download_path)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            for episode in downloader.get_episodes(tv_name, base_url, seasons):
                executor.submit(Episode.download, episode, download_path)
    finally:       
        SdarotDownloader.close_driver()

if __name__ == '__main__':
    download()