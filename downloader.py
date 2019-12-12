from selenium import webdriver
import requests
import time
import re
import os
from tqdm import tqdm
from selenium.webdriver.chrome.options import Options
    

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(chrome_options=options)

def get_download_links(page_link, seasons = None):
    """
    The function will get the download links for spesific seasons
    :param page_link: link to the page of the tv show in sdarot
    :seasons: list of seasons to download (if not specified it will download every season)
    :return: The function will return a generator that generates the download links in the following dict format 
    {season: season_number, episode: episode_number, video_link:link to the video, cookies: driver cookies, format:file format}
    """
    driver.get(page_link)
    seasons_links = [s.get_attribute('href') for s in driver.find_elements_by_xpath(r'//*[@id="season"]/li[*]/a')]
    if seasons == None: #if the user decide to download all seasons
        seasons = range(1, len(seasons_links) + 1)

    for season_number in seasons:
        assert 0 < season_number <= len(seasons_links), f"Invalid season number {season_number}" #TODO validate season numbers
        season = seasons_links[season_number - 1]
        driver.get(season)
        episodes_links = [e.get_attribute('href') for e in driver.find_elements_by_xpath(r'//*[@id="episode"]/li[@*]/a')] #getting episode pages link
        for link in episodes_links:
            episode = {}
            header = re.split('([0-9]+)/episode/([0-9]+)', link)[1:3]
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


def search(keyword): 
    """
    The function will scrape data from the search enginge in sdarot
    :param keyword: the string to search
    :return: dictionary ({'title of the tv show' : (hebrew name, year it went live, link to the tv show page on sdarot)})
    """
    base = 'https://sdarot.world/search?term='
    global driver
    driver.get(base + keyword.replace(' ', '+'))
    links = {}
    
    if '/watch/' in driver.current_url: #Case that there was only one result (if there is only one result sdarot redirect the website to the tv show page)
        name = driver.find_element_by_xpath(r'//*[@id="watchEpisode"]/div[1]/div/h1').text
        name = name.split(' / ')
        heb_name = name[0][::-1]
        name = name[1]
        date = driver.find_element_by_id('year').text
        links[name] = (heb_name, date, driver.current_url)
        return links

    for result in driver.find_elements_by_xpath(r'//*[@id="seriesList"]/div[*]/div/div[*]/div'):
        name = result.find_element_by_tag_name('h5').get_attribute('innerHTML') #title of the tv show
        heb_name = result.find_element_by_tag_name('h4').get_attribute('innerHTML')[::-1] #getting the hebrew name of the tv show
        date = re.search(r'[0-9]+', result.find_element_by_tag_name('p').get_attribute('innerHTML')).group() # get the year the tv show got out
        link = result.find_element_by_tag_name('a').get_attribute('href')
        links[name] = (heb_name, date, link)
    return links
