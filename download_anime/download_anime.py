import os
import sys
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as cond
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
import time
from absl import flags
import json
from absl import app
import urllib.request
import re

FLAGS = flags.FLAGS

flags.DEFINE_string('anime', None, 'Enter the name of the anime according to the website')
flags.DEFINE_integer('start', 1, 'Enter the start episode number(inclusive) to download')
flags.DEFINE_integer('end', -1, 'Enter the end episode number(inclusive) to download')
flags.DEFINE_string('site', '4anime', 'Enter which site to download from: 4anime or kissanime (Recommended 4anime)')


class FourAnime():

	def __init__(self, config):
		self.options = webdriver.ChromeOptions()
		self.driver = webdriver.Chrome(options = self.options)
		self.driver.maximize_window()
		self.anime = FLAGS.anime
		self.start = FLAGS.start
		self.download_dest = os.path.join(config["destination_path"], self.anime)
		self.end = FLAGS.end
		self.not_downloaded = []
		self.total_episodes = 0		

	def checkExists(self):
		WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.ID, 'headerDIV_2')))
		all_divs = self.driver.find_elements_by_id('headerDIV_2')
		if len(all_divs) > 1:
			WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//div[text() = "{}"]/ancestor::a'.format(self.anime))))
			site = self.driver.find_element_by_xpath('//div[text() = "{}"]/ancestor::a'.format(self.anime))
			site.click()

		else:
			print('Unable to find anime. Enter the anime as found in 4anime site')
			exit()

	def getTotalAssert(self):
		WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//ul[@class = "episodes range active"]//li')))		
		episode_list = self.driver.find_elements_by_xpath('//ul[@class = "episodes range active"]//li')
		self.total_episodes = len(episode_list)
		if self.end == -1:
			self.end = self.total_episodes

		if self.end > self.total_episodes:
			self.end = self.total_episodes

		if self.start < 1:
			self.start = 1

		assert self.start <= self.end


	def retrieve(self):
		self.driver.get('https://4anime.to/')	
		WebDriverWait(self.driver, timeout = 100).until(cond.title_is('4Anime - Watch anime online'))
		search_box = self.driver.find_element_by_xpath('//*[@id="ajaxsearchlite2"]/div/div[2]/form/input[1]')
		search_box.send_keys(self.anime)
		search_box.send_keys(Keys.RETURN)
		self.checkExists()
		self.getTotalAssert()	

		for episode in range(self.start, self.end + 1):
			current_episode = self.driver.find_elements_by_xpath('//ul[@class = "episodes range active"]//li')[episode - 1].find_element_by_xpath('.//a')
			ep_num = current_episode.text
			current_episode.click()

			WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//main[@id = "main"]/section/article/div/div[2]/a[text() = " Download"]')))		
			download = self.driver.find_element_by_xpath('//main[@id = "main"]/section/article/div/div[2]/a[text() = " Download"]')
			download.click()

			video = self.driver.find_element_by_xpath('//video/source')
			url = video.get_attribute('src')
			self.driver.back()	
			print('Downloading Episode {}...'.format(ep_num))
			try:
				if not os.path.exists(self.download_dest):
					os.mkdir(self.download_dest)
				urllib.request.urlretrieve(url, os.path.join(self.download_dest, "{} Episode {}.mp4".format(self.anime, ep_num)))
			except Exception as e:
				print('Unable to download Episode {}'.format(ep_num))
				self.not_downloaded.append(ep_num)
				continue

		self.driver.quit()
		if len(self.not_downloaded) > 0:
			print('Episodes not downloaded: ', *self.not_downloaded)		




class KissAnime():
	pattern = re.compile(r'.+([\d]+)')

	def __init__(self, config):
		options = webdriver.ChromeOptions()
		options.add_argument('disable-popup-blocking')
		options.add_extension('./AdBlock — best ad blocker.crx')
		options.add_argument('--ignore-certificate-errors')
		options.add_argument('--ignore-ssl-errors')	
		self.download_dest = os.path.join(config["destination_path"], FLAGS.anime)
		prefs = {"download.prompt_for_download": False, "download.default_directory": self.download_dest, "download.directory_upgrade": True}		
		options.add_experimental_option('prefs', prefs)

		self.options = options		
		self.prefs = prefs
		self.start = FLAGS.start
		self.anime = FLAGS.anime
		self.end = FLAGS.end
		self.not_downloaded = []
		self.total_episodes = 0
		self.driver = None


	def checkExists(self):
		content = self.driver.page_source
		if not 'No tags found' in content:
			WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//a[text() = "\n{}"]'.format(self.anime + ' (Sub)'))))
			site = self.driver.find_element_by_xpath('//a[text() = "\n{}"]'.format(self.anime + ' (Sub)'))
			site.click()
		else:
			print('Unable to find anime. Enter the anime as found in kissanime site')
			exit()

	def expandShadowElement(self, element):
		shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', element)
		return shadow_root

	def getTotalAssert(self):
		WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//*[@id="leftside"]/div[3]/div[2]/div[2]/table/tbody/tr')))
		episode_list = self.driver.find_elements_by_xpath('//*[@id="leftside"]/div[3]/div[2]/div[2]/table/tbody/tr')
		self.total_episodes = len(episode_list) - 2
		if self.end == -1:
			self.end = self.total_episodes

		if self.end > self.total_episodes:
			self.end = self.total_episodes

		if self.start < 1:
			self.start = 1

	def getEpisodeNum(self, current_episode):
		txt = current_episode.text
		ep_num = txt.split(' ')[-1]
		return ep_num

	def clean(self):
		time.sleep(1)
		handles = self.driver.window_handles
		while len(handles) > 1:
			execute = handles.pop()
			self.driver.close()
			self.driver.switch_to_window(self.driver.window_handles[-1])

	def retrieve(self):
		driver = webdriver.Chrome(options = self.options) 
		self.driver = driver
		self.clean()
		self.driver.get('https://www.kiss-anime.ws/')

		self.driver.maximize_window()

		WebDriverWait(self.driver, timeout = 100).until(cond.title_contains('KissAnime - Watch Anime Online English Subbed & Dubbed'))

		search_box = self.driver.find_element_by_xpath('//*[@id="keyword"]')
		search_box.send_keys(self.anime)
		search_box.send_keys(Keys.RETURN)
		self.checkExists()
		self.getTotalAssert()
	
		for episode in range(self.start, self.end + 1):
			WebDriverWait(self.driver, 20).until(cond.presence_of_element_located((By.XPATH, '//*[@id="leftside"]/div[3]/div[2]/div[2]/table/tbody/tr')))
			current_episode = self.driver.find_elements_by_xpath('//*[@id="leftside"]/div[3]/div[2]/div[2]/table/tbody/tr')[self.total_episodes + 2 - episode].find_element_by_xpath('.//td//a')
			ep_num = self.getEpisodeNum(current_episode)
			current_episode.click()

			WebDriverWait(self.driver, 20).until(cond.visibility_of_element_located((By.XPATH, '//div[@id="divDownload"]//a')))
			video = self.driver.find_element_by_xpath('//div[@id="divDownload"]//a')
			current_url = self.driver.current_url			

			video.click()
			if driver.current_url != current_url:
				check =  self.driver.page_source
				if '404 Not Found' or 'ERROR 404' in check:
					self.not_downloaded.append(ep_num)
					print('Unable to download Episode {}'.format(ep_num))
					self.driver.back()
					self.driver.back()
					continue

			print('Downloading Episode {}...'.format(ep_num))
			self.driver.get("chrome://downloads/")
			WebDriverWait(self.driver, 20).until(cond.title_is('Downloads'))

			root1 = self.driver.find_element_by_tag_name('downloads-manager')
			shadow_root1 = self.expandShadowElement(root1)
			WebDriverWait(shadow_root1, 20).until(cond.presence_of_element_located((By.ID, 'frb0')))
			root2 = shadow_root1.find_element_by_id('frb0')
			shadow_root2 = self.expandShadowElement(root2)
			status = shadow_root2.find_element_by_id("description")
			length = len(status.text)

			while length >= 1:
				status = shadow_root2.find_element_by_id("description")
				length = len(status.text)

			self.driver.back()
			self.driver.back()

		self.driver.quit()
		if len(self.not_downloaded) > 0:
			print('Episodes not downloaded: ', *self.not_downloaded)

def main(argv):
	sites = ['https://www.kiss-anime.ws/', 'https://4anime.to/']
	with open("config.json") as fp:
		config = json.load(fp)

	if FLAGS.site == '4anime':
		four_anime= FourAnime(config)
		four_anime.retrieve()
	elif FLAGS.site == 'kissanime':
		kiss_anime = KissAnime(config)
		kiss_anime.retrieve()

	
if __name__ == '__main__':
	flags.mark_flag_as_required('anime')
	app.run(main)