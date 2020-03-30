from downloader import SdarotDownloader
import click
import cutie
import re
import os
from winreg import *


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
        if seasons:
            seasons = [int(x) for x in seasons.split(',')]
    except ValueError: #Case that season number was not int
        raise click.BadParameter('Seasons must be a number')   
    except SdarotDownloader.NoResultsFound as e:
        raise click.BadOptionUsage(e)
    else:
        print('Downloading:', tv_name)
        download_path = os.path.join(download_path, tv_name)
        if not os.path.isdir(download_path):
            os.mkdir(download_path)
        os.chdir(download_path)
        for episode in downloader.get_episodes(tv_name, base_url, seasons):
            episode.download(download_path)
    finally:       
        SdarotDownloader.close_driver()

if __name__ == '__main__':
    download()