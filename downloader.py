from selenium import webdriver
import requests
import time
import re
import os
from tqdm import tqdm
from selenium.webdriver.chrome.options import Options
import itertools

class SdarotDownloader:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(chrome_options=options)

    class NoResultsFound(Exception):
        def __init__(self, keyword):
            self._keyword = keyword
        
        def __str__(self):
            return f'No results found for: "{self._keyword}"'

    class InvalidParams(Exception):
        def __init__(self, season, episode = None):
            self._season = season
            self._episode = episode
        
        def __str__(self):
            if self._episode:
                return f'Episode not found S{self._season}E{self._episode}'
            return f'Season not found - Season {self._season}'

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
    def get_episodes(cls, tv_name, links):
        """
        The function will get the the episodes for a season
        :param tv_name: the name of the tv show (str)
        :param links: the links to download the episodes from (list of str)
        :return: generator that generates Episode classes for each episode
        """
        for link in links:
            season_number, episode_number = re.split('([0-9]+)/episode/([0-9]+)', link)[1:3]
            cls.driver.get(link)
            cls.countdown()
            video_link = cls.driver.find_element_by_tag_name('video').get_attribute('src')
            cookie = cls.driver.get_cookies()
            yield Episode(tv_name, season_number, episode_number, video_link, cookie, 'mp4')

    @classmethod
    def get_links_for_episodes(cls, page_link, seasons):
        """
        Helper function that will parse the input and retrive links for the get_episodes function
        :param page_link: link for the tv show page (str)
        :param seasons: the structure to parse (defaultdict)
        :return: links of the episodes to download
        :raise: InvalidParams if one of the paramaeters was not valid
        """
        cls.driver.get(page_link)
        seasons_links = [s.get_attribute('href') for s in cls.driver.find_elements_by_xpath(r'//*[@id="season"]/li[*]/a')]
        links = []
        if seasons:
        	seasons = seasons.items()
        else:
            seasons = zip(range(1, len(seasons_links) + 1), itertools.repeat(set())) # Creating a dict that means download everything

        for season, episodes in seasons:
            if 0 >= season  or season > len(seasons_links):
                raise cls.InvalidParams(season)
            cls.driver.get(seasons_links[season -1])
            episodes_links = [e.get_attribute('href') for e in cls.driver.find_elements_by_xpath(r'//*[@id="episode"]/li[@*]/a')] 
            if episodes:
                for episode in episodes:
                    if 0 >= episode or episode > len(episodes_links):
                        raise cls.InvalidParams(season, episode)
                    links.append(episodes_links[episode - 1])
            else:
                links += episodes_links
        return links

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
        dir_name = 'Season ' + self._season_number
        if not os.path.isdir(dir_name):
            print('Downloading', dir_name)
            os.mkdir(dir_name)
        path = os.path.join(path, dir_name)

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