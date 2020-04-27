from downloader import SdarotDownloader, Episode
import click
import os
import concurrent.futures
from utils import *


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--seasons', default=None, help="Seasons to download, divided by comma")
@click.option('--download-path', default=get_download_path(), help='Set the downlaod path, by default download path is set to Download folder')
@click.argument('tv_show')
def download(seasons, download_path, tv_show):
    """This script will download tv shows from sdarot tv website
    TV_SHOW is the name of the tv show to download
    """
    #NOTE use the link from a confiig file, add download path to SdarotDownloader class
    downloader = SdarotDownloader('https://sdarot.world/')
    try:
        tv_name, base_url = get_one_result(downloader, tv_show)
        links = downloader.get_links_for_episodes(base_url, parse_seasson_input(seasons))
    except ValueError: #Case that season number was not int
        raise click.BadParameter('Seasons must be a number')   
    except Exception as e:
        raise click.UsageError(e)
    else:
        print('Downloading:', tv_name)
        download_path = os.path.join(download_path, tv_name)
        print('Download path:', download_path)
        if not os.path.isdir(download_path):
            os.mkdir(download_path)
        os.chdir(download_path)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            for episode in downloader.get_episodes(tv_name, links):
                executor.submit(Episode.download, episode, download_path)
    finally:       
        SdarotDownloader.close_driver()

if __name__ == '__main__':
    download()