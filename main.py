from downloader import SdarotDownloader
import click
import cutie
import re
import os
from winreg import *


class NoResults(Exception): #Will be thrown if no results were found in a search query
    pass


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
    if not search_results:
        raise NoResults
    click.echo('Select TV show to download')    
    results_names = list(search_results.keys())    
    formated_names = [f'{name} - {search_results[name][0]} ({search_results[name][1]})' for name in  results_names] + ['Exit']
    index = cutie.select(formated_names)
    if index == len(results_names): #if user wants to exit
        exit()
    tv_name = results_names[index]
    base_url = search_results[tv_name][2]
    tv_name = re.sub(r'[/\\:*?"<>|]', '', tv_name) #turning the string into a valid file name for windows
    return (tv_name, base_url)


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
    except NoResults:
        raise click.BadOptionUsage('No results found')
    else:
        os.mkdir(os.path.join(download_path, tv_name))
        os.chdir(os.path.join(download_path, tv_name))

        for episode in downloader.get_episodes(tv_name, base_url, seasons):
            episode.download(download_path)
    finally:       
        SdarotDownloader.close_driver()

if __name__ == '__main__':
    download()