import downloader
import click
import cutie
import re
import os


class NoResults(Exception): #Will be thrown if no results were found in a search query
    pass

@click.command()
@click.option('--seasons', default=None, help="Seasons to download, divided by comma")
@click.argument('tv_show')
def download(seasons, tv_show):
    print(seasons)
    try:
        tv_name, base_url = get_one_result(tv_show)
        if seasons:
            seasons = [int(x) for x in seasons.split(',')]
        for episode in downloader.get_download_links(base_url, seasons):
            download_path = f"{tv_name} S{episode['season']:0>2}"
            if not os.path.exists(download_path):
                os.mkdir(download_path)
            downloader.download_video(episode['video_link'], f"{tv_name} S{episode['season']:0>2}E{episode['episode']:0>2}.{episode['format']}", episode['cookies'], download_path)
    except ValueError: #Case that season number was not int
        raise click.BadParameter('Seasons must be a number')   
    except NoResults:
        raise click.BadOptionUsage('No results found')
    


def get_one_result(tv_show):
    """
    The function will get a spesific result from the search query
    :param tv_show: the name of the tv show (str)
    :return: tv_name, base_url (tupple)
    """
    search_results = downloader.search(tv_show)
    if not search_results:
        raise NoResults
    print('Select TV show to download')    
    results_names = list(search_results.keys())    
    formated_names = list(map(lambda name : f'{name} - {search_results[name][0]} ({search_results[name][1]})', results_names)) + ['Exit']
    index = cutie.select(formated_names)
    if index == len(results_names): #if user wants to exit
        exit()
    tv_name = results_names[index]
    base_url = search_results[tv_name][2]
    tv_name = re.sub(r'[/\\:*?"<>|]', '', tv_name) #turning the string into a valid file name for windows
    return (tv_name, base_url)

if __name__ == '__main__':
    download()