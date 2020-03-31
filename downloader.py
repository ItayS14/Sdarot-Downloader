from selenium import webdriver
import requests
import time
import re
import os
from tqdm import tqdm
from selenium.webdriver.chrome.options import Options


class SdarotDownloader:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(chrome_options=options)

    class NoResultsFound(Exception):
        def __init__(self, keyword):
            self._keyword = keyword
        
        def __str__(self):
            return f'No results found for: "{self._keyword}"'

    def __init__(self, base_url):
        self._base_url = base_url

    def search(self, keyword): 
        """
        The function will scrape data from the search enginge in sdarot
        :param keyword: the string to search
        :return: list of TVShowMetaData for each result
        """
        self.driver.get(self._base_url + 'search?term=' + keyword.replace(' ', '+'))
        
        if '/watch/' in self.driver.current_url: #Case that there was only one result (if there is only one result sdarot redirect the website to the tv show page)
            heb_name, name = self.driver.find_element_by_xpath(r'//*[@id="watchEpisode"]/div[1]/div/h1').text.split(' / ')
            heb_name = heb_name
            date = self.driver.find_element_by_id('year').text
            return [TVShowMetaData(name, heb_name, date, self.driver.current_url)]

        links = []
        for result in self.driver.find_elements_by_xpath(r'//*[@id="seriesList"]/div[*]/div/div[*]/div'):
            name = result.find_element_by_tag_name('h5').get_attribute('innerHTML') #title of the tv show
            heb_name = result.find_element_by_tag_name('h4').get_attribute('innerHTML') #getting the hebrew name of the tv show
            date = re.search(r'[0-9]+', result.find_element_by_tag_name('p').get_attribute('innerHTML')).group() # get the year the tv show got out
            link = result.find_element_by_tag_name('a').get_attribute('href')
            links.append(TVShowMetaData(name, heb_name, date, link))

        if not links:
            raise self.NoResultsFound(keyword)
        return links

    @classmethod
    def get_episodes(cls, tv_name, page_link, seasons = None):
        """
        The function will get the the episodes for a season
        :param page_link: link to the page of the tv show in sdarot
        :seasons: list of seasons to download (if not specified it will download every season)
        :return: generator that generates Episode classes for each episode
        """
        cls.driver.get(page_link)
        seasons_links = [s.get_attribute('href') for s in cls.driver.find_elements_by_xpath(r'//*[@id="season"]/li[*]/a')]
        if seasons == None: #if the user decide to download all seasons
            seasons = range(1, len(seasons_links) + 1)

        for season_number in seasons:
            assert 0 < season_number <= len(seasons_links), f"Invalid season number {season_number}" #TODO validate season numbers
            season = seasons_links[season_number - 1]
            cls.driver.get(season)
            episodes_links = [e.get_attribute('href') for e in cls.driver.find_elements_by_xpath(r'//*[@id="episode"]/li[@*]/a')] #getting episode pages link
            for link in episodes_links:
                season_number, episode_number = re.split('([0-9]+)/episode/([0-9]+)', link)[1:3]
                cls.driver.get(link)
                cls.countdown()
                video_link = cls.driver.find_element_by_tag_name('video').get_attribute('src')
                cookie = cls.driver.get_cookies()
                yield Episode(tv_name, season_number, episode_number, video_link, cookie, 'mp4')

    @classmethod
    def countdown(cls):
        """
        countdown function for sdarot, it will wait the require 30 seconds until the video is viewable 
        """
        timer = float(cls.driver.find_element_by_xpath(r'//*[@id="waitTime"]/span').get_attribute('outerText'))
        while timer != 0:
            timer = float(cls.driver.find_element_by_xpath(r'//*[@id="waitTime"]/span').get_attribute('outerText'))
        time.sleep(2)

    @classmethod
    def close_driver(cls):
        """
        The function will close the open driver
        """
        cls.driver.close()


class Episode:
    def __init__(self, tv_name, season_number, episode_number, link, cookies, format):
        self._tv_name = tv_name.replace(':', '-') # Maybe change it to the TVShowMetaData class
        self._season_number = season_number
        self._episode_number = episode_number
        self._link = link
        self._cookies = cookies
        self._format = format

    def download(self, path=""):
        """
        The function will download the episode specified in the class
        """
        s = requests.Session()
        for cookie in self._cookies:
            s.cookies.set(cookie['name'], cookie['value'])
        response = s.get(self._link, stream = True)

        total_size = int(response.headers['content-length'])
        chunk_size = 1024
        with open(os.path.join(path, str(self)), 'wb') as f:  
            for data in tqdm(iterable=response.iter_content(chunk_size=chunk_size), desc=str(self), total=total_size / chunk_size, unit='KB'):
                f.write(data)

    def __str__(self):
         return f"{self._tv_name} S{self._season_number:0>2}E{self._episode_number:0>2}.{self._format}"


class TVShowMetaData:
    def __init__(self, name, heb_name, date, link):
        self._name = re.sub(r'[/\\:*?"<>|]', '', name) #turning the string into a valid file name for windows
        self._heb_name = heb_name[::-1] # Hebrew name need to be reversed
        self._date = date
        self._link = link
    
    @property
    def full_name(self):
        return self._name + ' - ' + self._heb_name

    def __str__(self):
        return f'{self.full_name} ({self._date})'

    # No next method is implemented, the iter is used to implement tupple unpacking like behavior
    def __iter__(self):
        return iter((self._name, self._link))