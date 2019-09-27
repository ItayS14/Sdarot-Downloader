from selenium import webdriver
import requests
import time
import re
import os
from tqdm import tqdm
import colorama
from colorama import Style, Fore
from selenium.webdriver.chrome.options import Options
import yaml

#TODO: build cli (That would support for now downloading full seriers, spesific seasons or spesific episodes)
#TODO: Thread the downloading, allow only one download at a time (optional, add every new link into the queue and then use Event object)
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(chrome_options=options)

with open('config.yaml') as f:
    config = yaml.load(f)


def main():
    global driver
    baseUrl = ""
    tv_name = input('Enter tv show to download: ')
    search_results = search(tv_name)
    if not search_results:
        print('No results found')
        return
    while True:
        results_names = list(search_results.keys())
        for i in range(len(results_names)):
            print(f'{i} - {results_names[i]} - {search_results[results_names[i]][0]} ({search_results[results_names[i]][1]})')
        selection = input('Enter the correct tv show index: ')
        if selection.isdigit() and 0 <= int(selection) < len(results_names):
            tv_name = results_names[int(selection)]
            baseUrl = search_results[tv_name][2]
            break
        print('Invalid option try again') #code is working
    tv_name = re.sub(r'[/\\:*?"<>|]', '', tv_name) #turning the string into a valid file name for windows

    os.chdir(config['default download path']) 
    os.mkdir(tv_name)
    os.chdir(tv_name)

    for episode in get_download_links(baseUrl):
        download_path = f"{tv_name} S{episode['season']:0>2}"
        if not os.path.exists(download_path):
            os.mkdir(download_path)
            print(Fore.BLUE + f"Downloading {tv_name} Season {episode['season']}")
            print(Style.RESET_ALL)
        download_video(episode['video_link'], f"{tv_name} S{episode['season']:0>2}E{episode['episode']:0>2}.{episode['format']}", episode['cookies'], download_path)
    driver.close()


def get_download_links(page_link, seasons = None):
    """
    The function will get the download links for spesific seasons
    :param page_link: link to the page of the tv show in sdarot
    :seasons: list of seasons to download (if not specified it will download every season)
    :return: The function will return a generator that generates the download links in the following dict format 
    {season: season_number, episode: episode_number, video_link:link to the video, cookies: driver cookies, format:file format}
    """
    driver.get(page_link)
    seasons_links = list(map(lambda s: s.get_attribute('href'), driver.find_elements_by_xpath(r'//*[@id="season"]/li[*]/a')))
    if seasons == None: #if the user decide to download all seasons
        seasons = range(1, len(seasons_links) + 1)

    for season_number in seasons:
        assert 0 < season_number <= len(seasons_links), f"Invalid season number {season_number}" #TODO validate season numbers
        season = seasons_links[season_number - 1]
        driver.get(season)
        episodes_links = list(map(lambda e: e.get_attribute('href'), driver.find_elements_by_xpath(r'//*[@id="episode"]/li[@*]/a'))) #getting episode pages link
        for link in episodes_links:
            episode = {}
            header = re.split('([0-9]+)/episode/([0-9])', link)[1:3]
            episode['season'] = header[0]
            episode['episode'] = header[1]
            driver.get(link)
            countdown()
            episode['video_link'] = driver.find_element_by_tag_name('video').get_attribute('src')
            episode['cookies'] = driver.get_cookies()
            episode['format'] = 'mp4' #TODO change it to correct file format
            yield (episode)


def download_video(url, name, cookies, path=""):
    """
        The function will download a video url with spesific cookies
        :param url: the url of the video to download
        :param name: the name of output file
        :param cookies: supplied cookied for the download
        :param path: The path to download the file to (if not specified will be in current directory)
    """
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    response = s.get(url, stream = True)
    name = name.replace(':', '-')
    total_size = int(response.headers['content-length'])
    chunk_size = 1024
    with open(os.path.join(path, name), 'wb') as f:  
         for data in tqdm(iterable=response.iter_content(chunk_size=chunk_size), desc=name, total=total_size / chunk_size, unit='KB'):
            f.write(data)

    
def countdown():
    """
    countdown function for sdarot, it will wait the require 30 seconds until the video is viewable 
    """
    global driver
    timer = float(driver.find_element_by_xpath(r'//*[@id="waitTime"]/span').get_attribute('outerText'))
    while timer != 0:
        print(f'{timer} Seconds remaining', end='\r')
        timer = float(driver.find_element_by_xpath(r'//*[@id="waitTime"]/span').get_attribute('outerText'))
    time.sleep(2)
    print()


def search(keyword): #TODO: get content if its only one result
    """
    The function will scrape data from the search enginge in sdarot
    :param keyword: the string to search
    :return: dictionary ({'title of the tv show' : (hebrew name, year it went live, link to the tv show page on sdarot)})
    """
    base = config['sdarot base url'] + 'search?term=' #TODO: change the link (http://sdarot.world/) to be read from config file
    global driver
    driver.get(base + keyword.replace(' ', '+'))
    assert r'/watch/' not in driver.current_url, "Only one result"
    links = {}
    for result in driver.find_elements_by_xpath(r'//*[@id="seriesList"]/div[*]/div/div[*]/div'):
        name = result.find_element_by_tag_name('h5').get_attribute('innerHTML') #title of the tv show
        heb_name = result.find_element_by_tag_name('h4').get_attribute('innerHTML')[::-1] #getting the hebrew name of the tv show
        date = re.search(r'[0-9]+', result.find_element_by_tag_name('p').get_attribute('innerHTML')).group() # get the year the tv show got out
        link = result.find_element_by_tag_name('a').get_attribute('href')
        links[name] = (heb_name, date, link)
    return links

if __name__ == '__main__':
    main()