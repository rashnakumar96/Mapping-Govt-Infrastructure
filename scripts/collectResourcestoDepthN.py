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
import pathlib
import statistics
import findcdn
import psutil
import csv


from collections import defaultdict
import socket
import ssl
from webdriver_manager.chrome import ChromeDriverManager
from browsermobproxy.exceptions import ProxyServerError
from selenium.common.exceptions import TimeoutException, WebDriverException

project_path = os.path.dirname(os.path.abspath(__file__))

print (project_path)

def create_dir_if_not_exists(path):
	pathlib.Path(path).mkdir(parents=True, exist_ok=True)

class HARGenerator():
    # This class is used to interact with BrowserMob Proxy, see here: https://github.com/lightbody/browsermob-proxy
    # Source code for Python API is: https://browsermob-proxy-py.readthedocs.io/en/latest/_modules/browsermobproxy/server.html#Server
    # Please make sure your system has the required Java runtime for the server to run properly.

	def __init__(self):
		self.port = 8090
		self.bmp_log_path = os.path.join(project_path, '..', 'logs', 'bmp')
		create_dir_if_not_exists(self.bmp_log_path)
		self.chrome_driver_log_path = os.path.join(project_path, '..', 'logs', 'chromedriver')
		create_dir_if_not_exists(self.chrome_driver_log_path)
		self.terminated = False

		try:
			# Pen.write(f"Initiating server...", color='OKGREEN', newline=False)
			self.server = Server(
			    # path=os.path.join(project_path, '..', 'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy'),
			    path=os.path.join(project_path,'browsermob-proxy-2.1.4', 'bin', 'browsermob-proxy'),
			    options={'port': self.port})
            # Pen.write(f"OK", color='OKGREEN')

            # Pen.write(f"Starting server...", color='OKGREEN', newline=False)
			self.server.start(options={
			    'log_file': f'{datetime.now().strftime("%Y-%m-%d-%H:%M:%S")}.log',
			    'log_path': self.bmp_log_path,
			    'retry_count': 5
			})
            # Pen.write(f"OK", color='OKGREEN')

		except ProxyServerError as err:
            # Pen.write(f"Error starting server. Please check server logs. Exiting...", color='FAIL')
            # Pen.write(str(err), color='FAIL')
			print (str(err))
			exit(-1)

        # Pen.write(f"Creating proxy server...", color='OKGREEN', newline=False)
		self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
        # Pen.write(f"OK", color='OKGREEN')

        # Pen.write(f"Creating Chrome driver...", color='OKGREEN', newline=False)
		self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=self._chrome_options())
        # Pen.write(f"OK", color='OKGREEN')

	def _chrome_options(self):
		options = webdriver.ChromeOptions()
		options.add_argument("--proxy-server={}".format(self.proxy.proxy))
		options.add_argument("--ignore-ssl-errors=yes")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument("--headless")
		options.add_argument("--no-cache")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--verbose")
		options.add_argument(f"--log-path={self.chrome_driver_log_path}")

		return options

	def __del__(self):
		if not self.terminated:
            # Pen.write(
            #     f"Clean up on HARGenerator object deletion. Did you forget to explicitly terminate HARGenerator object?",
            #     color='WARNING')
			self.terminate()

	def terminate(self):
		try:
            # BrowserMobProxy starts a process (parent process), which starts another process running the proxy server (child process)
            # Calling self.server.stop() only stops the parent process but not the child process, which becomes a zombie process when the program ends
            # Pen.write(f"Cleaning up HAR object...", color='OKGREEN')

			for child in psutil.Process(self.server.process.pid).children(recursive=True):
                # Pen.write(f"Killing child process {child.pid}...", color='OKGREEN', newline=False)
				child.kill()
                # Pen.write(f"OK", color='OKGREEN')
            # Pen.write(f"Killing BMP server...", color='OKGREEN', newline=False)
			self.server.stop()
            # Pen.write(f"OK", color='OKGREEN')

            # Pen.write(f"Killing Chrome driver...", color='OKGREEN', newline=False)
			self.driver.quit()
			time.sleep(1)  # This is to prevent "ImportError: sys.meta_path is None, Python is likely shutting down" from Selenium, see here: https://stackoverflow.com/questions/41480148/importerror-sys-meta-path-is-none-python-is-likely-shutting-down
			# Pen.write(f"OK", color='OKGREEN')

			self.terminated = True
		# except ImportError:
		# 	pass  # Ignore "ImportError: sys.meta_path is None, Python is likely shutting down"
		except Exception as e:
			print (str(e))

    # def get_har(self, hostname):
    #     self.proxy.new_har(hostname)
    #     try:
    #         self.driver.set_page_load_timeout(60)
    #         self.driver.get(f'https://{hostname}')
    #     except TimeoutException as err:
    #         Pen.write(f'Timeout from renderer for {hostname}. Skipping...', 'FAIL')
    #     except WebDriverException as err:
    #         Pen.write(f'ERR_TUNNEL_CONNECTION_FAILED from renderer for {hostname}. Skipping...', 'FAIL')
    #     except Exception as err:
    #         Pen.write(f'Unexpected error: {err}.\n Skipping...', 'FAIL')

    #     time.sleep(1)

    #     return self.proxy.har

    # def get_hars(self, hostnames):
    #     hars = list()
    #     for i, hostname in enumerate(hostnames):
    #         hars.append(self.get_har(hostname))

    #     return hars

	def get_har(self, site):        
		try:
			name = site
			self.proxy.new_har(name)
			self.driver.set_page_load_timeout(60)
			self.driver.get(site)

			time.sleep(1)
			return self.proxy.har
		except Exception as e:
			print("Error in getting har: ",str(e))
			return None

        
    # calls get_har for each site
    # takes a list of site urls
    # returns a dictionary of site url and json har objects
	def get_hars(self, sites):
		x = 0
		hars = []
		for site in sites:
			har = self.get_har(site)
			hars.append(har)
			x = x + 1
		return hars

class Har_generator:
	def __init__(self):
		
		self.hars = []
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
		# find_and_kill_processes_by_port(9222)
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

    # loads up a site
    # takes a site url
    # returns a json har object
	def get_har(self, site):        
		try:
			name = site
			self.proxy.new_har(name)
			self.driver.set_page_load_timeout(60)
			self.driver.get(site)

			time.sleep(1)
			return self.proxy.har
		except Exception as e:
			print("Error in getting har: ",str(e))
			return None

        
    # calls get_har for each site
    # takes a list of site urls
    # returns a dictionary of site url and json har objects
	def get_hars(self, sites):
		x = 0
		hars = []
		for site in sites:
			har = self.get_har(site)
			hars.append(har)
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

# def collectResources(country, resourcesDict):
#     filename = DATA_PATH + '/alexaTop500SitesCountries.json'
#     hm = HARGenerator()

#     website_iter = 0

#     try:
#         websites = read_websites_country(country, filename)

#         for website in websites:
#             website_iter += 1
#             if website in resourcesDict:
#                 continue
#             Pen.write(
#                 f"Collecting resources for hostname: {website} Progress: {website_iter + 1}/{len(websites)} "
#                 f"({(website_iter + 1) * 100 / len(websites):.2f}%)", color='OKCYAN')
#             # Pen.write("country: " + country + " ,website: " + website + " ,num: " + str(website_iter), color='OKGREEN')
#             resourcesDict[website] = []
#             resources = get_resources(website, hm)
#             if resources == None:
#                 hm = HARGenerator()
#                 resources = get_resources(website, hm)
#             resourcesDict[website] = resources
#             dump_json(resourcesDict, 'results/resources/resources_' + country + '.json')
#     finally:
#         hm.terminate()

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
		# print (str(e))
		
	hm=Har_generator()
	# hm=HARGenerator()
	try:
		temphostnametoResourcesMap={}
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
	finally:
		# hm.terminate()
		print ("Done")

	
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

	