from selenium import webdriver
import requests
import time
import re
import os

#TODO: build cli (That would support for now downloading full seriers, spesific seasons or spesific episodes)
#TODO: add progress bar for the download
#TODO: add support for bad file names
#TODO: Thread the downloading, allow only one download at a time
driver = webdriver.Chrome('chromedriver.exe')

def main():
    global driver
    baseUrl = ""
    tv_name = input('Enter tv show to download: ')
    search_results = search(tv_name)
    print(search_results)
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
    for episode in get_download_links(baseUrl, [1,2]):
        print(episode)
        download_video(episode[1], f'{tv_name} {episode[0]}', episode[2])
    driver.close()


def get_download_links(page_link, seasons):
    """
    The function will get the download links for spesific seasons
    :param page_link: link to the page of the tv show in sdarot
    :seasons: list of seasons to download (if None it will download every season)
    :return: The function will return a generator that generates the download links in the following tupple format (episode header, episode video link, current driver cookies)
    """
    driver.get(page_link)
    seasons_links = list(map(lambda s: s.get_attribute('href'), driver.find_elements_by_xpath(r'//*[@id="season"]/li[*]/a')))
    if seasons == None: #if the user decide to download all seasons
        seasons = range(1, list(len(seasons_links) + 1))

    for season_number in seasons:
        assert 0 < season_number < len(seasons_links), "Invalid season number" #TODO validate season numbers
        season = seasons_links[season_number - 1]
        print('*', 'season ' ,season[season.rfind('/') + 1:] , '*')
        driver.get(season)
        episodes_links = list(map(lambda e: e.get_attribute('href'), driver.find_elements_by_xpath(r'//*[@id="episode"]/li[@*]/a'))) #getting episode pages link
        for episode in episodes_links[8:]:
            episode_header = episode[episode.find('season'):].replace('/', ' ').title()
            driver.get(episode)
            countdown()
            video_link = driver.find_element_by_tag_name('video').get_attribute('src')
            yield (f'{episode_header}.mp4', video_link, driver.get_cookies())


def download_video(url, name, cookies):
    """
        The function will download a video url with spesific cookies
        :param url: the url of the video to download
        :param name: the name of output file
        :param cookies: supplied cookied for the download
    """
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    response = s.get(url, stream = True)
    name = name.replace(':', '-')
    with open(name, 'wb') as f:  
        f.write(response.content)
    print(name, " Download complete")

    
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


def search(keyword): #TODO: add a condition that checks no resuls, only one result
    """
    The function will scrape data from the search enginge in sdarot
    :param keyword: the string to search
    :return: dictionary ({'title of the tv show' : (hebrew name, year it went live, link to the tv show page on sdarot)})
    """
    base = r'https://sdarot.world/search?term=' #TODO: change the link (http://sdarot.world/) to be read from config file
    global driver
    driver.get(base + keyword.replace(' ', '+'))
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