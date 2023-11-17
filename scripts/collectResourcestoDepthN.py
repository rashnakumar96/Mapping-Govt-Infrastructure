from browsermobproxy import Server
import os
from selenium import webdriver
from browsermobproxy import Client
from selenium.webdriver.chrome.options import Options
import requests
import time
from selenium.common.exceptions import WebDriverException
import json
import sys
from datetime import datetime
import dns.resolver
import tldextract
from bs4 import BeautifulSoup
import urllib.request
from os.path import isfile, join
import selenium.webdriver.remote.utils as utils
import subprocess
import re
from pathlib import Path
import statistics
import findcdn
import psutil
import csv


from collections import defaultdict
import socket
import ssl

class Har_generator:
	def __init__(self):
		
		self.hars = []
		# dict={'port':9222}
		# find_and_kill_processes_by_port(9222)
		dict={}
		current_directory = os.getcwd()
		self.server = Server(current_directory+"/scripts/browsermob-proxy-2.1.4/bin/browsermob-proxy",options=dict)
		self.server.start()
		self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
		options = Options()
		# options.add_argument("--proxy-server={}".format(self.proxy.proxy)) 
		options.add_argument(f'--proxy-server={self.proxy.proxy}')
		options.add_argument("--ignore-ssl-errors=yes")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument("--headless")
		options.add_argument("--remote-debugging-port=9222")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--no-cache")
		options.add_argument("--no-sandbox")        
		self.driver = webdriver.Chrome(options=options)


		#code for caitlyn
		# dict={'port':9222}
		# # find_and_kill_processes_by_port(9222)
		# current_directory = os.getcwd()
		# self.server = Server(current_directory+"/scripts/browsermob-proxy-2.1.4/bin/browsermob-proxy",options=dict)
		# self.server.start()
		# self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
		# chromedriver_path = '/usr/bin/chromedriver'
		# chrome_options = webdriver.ChromeOptions()
		# # chrome_options.binary_location = '/usr/bin/google-chrome'
		# chrome_options.add_argument(f'--proxy-server={self.proxy.proxy}')
		# chrome_options.add_argument("--ignore-ssl-errors=yes")
		# chrome_options.add_argument("--ignore-certificate-errors")
		# chrome_options.add_argument("--headless")
		# chrome_options.add_argument("--remote-debugging-port=9222")
		# chrome_options.add_argument("--disable-dev-shm-usage")
		# chrome_options.add_argument("--no-cache")
		# chrome_options.add_argument("--no-sandbox")

		# self.driver = webdriver.Chrome(options=chrome_options)


	def __del__(self):
		try:
			self.server.stop()
			self.driver.quit()
		except Exception as e:
			print (str(e))
			# self.restart_drive()


	def restart_drive(self):
		print("Restarting...")
		# self.driver.quit()
		# options = webdriver.ChromeOptions()
		options = Options()
		# options.add_argument("--proxy-server={}".format(self.proxy.proxy)) 
		options.add_argument(f'--proxy-server={self.proxy.proxy}')
		options.add_argument("--ignore-ssl-errors=yes")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument("--headless")
		options.add_argument("--remote-debugging-port=9222")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--no-cache")
		options.add_argument("--no-sandbox")        
		self.driver = webdriver.Chrome(options=options)

    # loads up a site
    # takes a site url
    # returns a json har object
	def get_har(self, site):        
		try:
			name = site
			self.proxy.new_har(name)
			self.driver.set_page_load_timeout(60)
			# self.driver.get("https://"+site)
			self.driver.get(site)

			time.sleep(1)
			return self.proxy.har
		except Exception as e:
			# try:
			# 	self.server.stop()
			# 	self.driver.quit()
			# 	time.sleep(1)
			# except Exception as e:
			# 	print (str(e))
			# hm=Har_generator()
			print("Error in getting har: ",str(e))
			return None

        
    # calls get_har for each site
    # takes a list of site urls
    # returns a dictionary of site url and json har objects
	def get_hars(self, sites):
		x = 0
		hars = []
		for site in sites:
			# print("%d: Working on %s" % (x, site))
			har = self.get_har(site)
			hars.append(har)
			# self.hars.append(har)
			x = x + 1
		return hars

class Resource_collector:
	def __init__(self):
		self.resources = []

    # extracts all the resources from each har object
    # takes a list of har json objects
    # stores in the object resources
	def collect_resources(self, har):
		try:
			if har and "log" in har.keys() and "entries" in har["log"].keys():
				for entry in har["log"]["entries"]:
					resource = entry["request"]["url"]
					if resource not in self.resources:
						self.resources.append(str(resource))
			return self.resources
		except:
			return None


def dump_json(data, fn):
    with open(fn, 'w') as fp:
        json.dump(data, fp)

def get_resources(website,hm):  
	#use hars to find resources!
	rc = Resource_collector()
	hars = hm.get_har(website)
	return rc.collect_resources(hars)

def updateJsonData(filename,tempDict):
	if os.path.exists(filename):
		with open(filename, 'r') as file:
			data = json.load(file)

		data.update(tempDict)

		file.close()

		with open(filename, 'w') as file:
			json.dump(data, file, indent=4)

		file.close()
	else:
		with open(filename, 'w') as file:
			json.dump(tempDict, file, indent=4)

		file.close()


def collectResources(country,hostnames,depth):
	try:
		filename='results/resources/hostnametoResourcesMap_'+country+'.json'
		with open(filename, 'r') as file:
			hostnametoResourcesMap = json.load(file)
		file.close()
		hostnamesDone=set(hostnametoResourcesMap.keys())
		hostnamesToProcess=set(hostnames)-hostnamesDone
		print (f"hostnames Done: {len(hostnamesDone)} hostnamesToProcess: {len(hostnamesToProcess)} total hostname passed to function: {len(hostnames)} at depth: {depth}")
	except Exception as e:
		hostnametoResourcesMap={}
		hostnamesToProcess=hostnames
		print (f"hostnamesToProcess: {len(hostnamesToProcess)} total hostname passed to function: {len(hostnames)} at depth: {depth}")
		print (str(e))

	temphostnametoResourcesMap={}
	hm=Har_generator()
	hostname_iter=0
	for hostname in hostnamesToProcess:
		print (f"At Depth {depth} of {country} and {100*hostname_iter/len(hostnamesToProcess)} % done")
		if hostname_iter%100==0:
			updateJsonData('results/resources/hostnametoResourcesMap_'+country+'.json',temphostnametoResourcesMap)	
			temphostnametoResourcesMap={}

		hostname_iter+=1
		try:
			resources=get_resources(hostname,hm)
			temphostnametoResourcesMap[hostname]=resources				
		except Exception as e:
			print (f"{hostname} Can't get Har of the hostname. Error: {str(e)}")
				
		
	updateJsonData('results/resources/hostnametoResourcesMap_'+country+'.json',temphostnametoResourcesMap)
	
	try:
		resourcesDictwDepth=json.load(open('results/resources/resources_'+str(depth)+"_"+country+'.json'))
	except:
		resourcesDictwDepth={}
	hostnametoResourcesMap=json.load(open('results/resources/hostnametoResourcesMap_'+country+'.json'))
	for hostname in hostnames:
		resourcesDictwDepth[hostname]=hostnametoResourcesMap[hostname]

	with open('results/resources/resources_'+str(depth)+"_"+country+'.json', 'w') as fp:
		json.dump(resourcesDictwDepth, fp)

	combined_list = []
	for values in resourcesDictwDepth.values():
		combined_list.extend(values)

	resourceList = list(set(combined_list))

	print ('\n')
	return resourceList

def find_and_kill_processes_by_port(port):
	for process in psutil.process_iter(attrs=['pid', 'name', 'connections']):
		try:
			process_info = process.info
			if process_info.get('connections') is not None:
				for conn in process.info['connections']:
					if conn.laddr.port == port:
						print(f"Found a process with PID {process.info['pid']} using port {port}.")
						try:
							process.terminate()
							print(f"Terminated the process with PID {process_info['pid']}.")
						except psutil.NoSuchProcess:
							print(f"Failed to terminate PID {process_info['pid'] (NoSuchProcess)}")
						except psutil.AccessDenied:
							print(f"Failed to terminate PID {process_info['pid'] (AccessDenied)}")
						except psutil.ZombieProcess:
							print(f"Failed to terminate PID {process_info['pid'] (ZombieProcess)}")
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass
						
def collectResourcestoDepthN(country, DEPTH_LEVEL):
	print(country)
	filename="data/dataset/"+country+"_govtWebsites.json"
	f = open(filename,'r') 
	data = json.load(f) 
	urls=data[country]
	f.close()
	
	for i in range(DEPTH_LEVEL):
		print (f"Crawling at depth: {i} and total number of urls are: {len(urls)}")
		urls=collectResources(country,urls,i)


def parseData(country,cc):
	filename=open("data/dataset/Govt.Infra -  Procesamiento - "+country+".csv",'r')
	file = csv.DictReader(filename)
	try:
		websitesData=json.load(open("data/dataset/"+cc+"_govtWebsites.json"))
		websites=set(websitesData[cc])
		print (len(websites))
	except:
		websites=set()

	for col in file:
		if col['URL']!="N/A":
			website=col['URL']
			if "http" not in website:
				website="https://"+website
			websites.add(website)
	dict={}
	dict[cc]=list(websites)
	with open("data/dataset/"+cc+"_govtWebsites.json", 'w') as fp:
		json.dump(dict, fp)
	print (len(websites))

def updateJsonData(filename,tempDict):
	if os.path.exists(filename):
		with open(filename, 'r') as file:
			data = json.load(file)

		data.update(tempDict)

		file.close()

		with open(filename, 'w') as file:
			json.dump(data, file, indent=4)

		file.close()
	else:
		with open(filename, 'w') as file:
			json.dump(tempDict, file, indent=4)

		file.close()

def runurls_content_size(urls,country):
	if not os.path.exists("results/urlSizeMap"):
		os.mkdir("results/urlSizeMap")
	try:
		urlSizeMap=json.load(open("results/urlSizeMap/urlSizeMap_" + country+ ".json"))
		urlsDone=set(urlSizeMap.keys())
		urls=set(urls)
		urlsToProcess=urls-urlsDone
	except:
		urlSizeMap={}
		urlsToProcess=urls
	
	print (f"urlsToProcess: {len(urlsToProcess)} total urls passed to function: {len(urls)}")

	counter=0
	tempurlSizeMap={}
	for url in urlsToProcess:
		counter+=1
		if counter%100==0:
			updateJsonData('results/urlSizeMap/urlSizeMap_' + country+ '.json',tempurlSizeMap)	
			tempurlSizeMap={}
			print ("written to file")
		print (f"{100*counter/len(urlsToProcess)} % of urls processed")
		content_length=get_content_size(url)
		if content_length==None:
			continue
		tempurlSizeMap[url]=content_length
	updateJsonData('results/urlSizeMap/urlSizeMap_' + country+ '.json',tempurlSizeMap)	

def get_content_size(url):
    try:
        response = requests.get(url, stream=True)  # Send a GET request and stream the content
        if 'Content-Length' in response.headers:
            # If Content-Length header is present, return it
            content_length = int(response.headers['Content-Length'])
        else:
            # If Content-Length is not present, calculate it based on the content
            content_length = len(response.content)

        return content_length
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None  # An error occurred

if __name__ == "__main__":
	country=sys.argv[1]
	CSVCountryName=sys.argv[2]

	if not os.path.exists("results"):
		os.mkdir("results")

	if not os.path.exists("results/resources"):
		os.mkdir("results/resources")

	parseData(CSVCountryName,country) #downloads data from the CSV into the format needed for processing

	DEPTH_LEVEL=7
	collectResourcestoDepthN(country, DEPTH_LEVEL) #collects all urls to the depth of seven

	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current End Time after collecting all Resources=", current_time)

	print (f"Now Finding the Size of all URLs")
	hostnametoResourcesMap=json.load(open('results/resources/hostnametoResourcesMap_'+country+'.json'))
	urls=set()
	for website in hostnametoResourcesMap:
		urls.add(website)
		for resource in hostnametoResourcesMap[website]:
			urls.add(resource)
	print (f"Number of unique urls for landing + internal pages: {len(urls)}")

	runurls_content_size(urls,country)

	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current End Time after Finding the Size of all URLs=", current_time)

	