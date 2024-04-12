import os
import requests
import time
import json
import sys
from datetime import datetime
import urllib.request
import socket
import ssl
from ipwhois import IPWhois
import ipaddress
from urllib.parse import urlparse
import signal
import subprocess


def timeout_handler(signum, frame):
    raise TimeoutError("A timeout has occurred! Waiting time has expired.")

def check_https_support(urls):
	HTTPSupportMap={}
	for url in urls:
		parsed_url = urlparse(url)
		domain = parsed_url.netloc
		CA=getCA(domain, retries=3)
		if CA: #if a website uses https, it presents the client with its ssl cert issued by a CA
			ans="HTTPS"
		else:
			try:
				response = requests.head(url)
				if response.status_code == 200:
					ans="HTTP"
				else:
					continue
			except Exception as e:
				print (str(e))
				continue
		HTTPSupportMap[url]=ans

	return HTTPSupportMap

def getCA(website, retries=3):
	try:
		output = subprocess.check_output(["openssl", "s_client", "-connect", website + ":443", "-status"],
		                                 timeout=15, input="", stderr=subprocess.STDOUT).decode("utf-8")

		rootCA = output.split("O = ")[1].split(" =")[0][:-4]
		if rootCA.startswith("\""):
			rootCA = rootCA[1:]
		if rootCA.endswith("\""):
			rootCA = rootCA[:-1]
		return rootCA.strip()
	except Exception as e:
		# print (str(e))
		if retries > 0:
			getCA(website, retries - 1)
		return None

def get_ip_address(domain):
	
	try:
		ip_address = socket.gethostbyname(domain)
		print(f"IP address of {domain} is {ip_address}")
	except Exception as e:
		print(f"Error:{str(e)} ;Failed to resolve IP address for {domain}")

	return ip_address

def get_AS_Org(urls):
	AS_OrgMap={}
	domains=set()
	for url in urls:
		parsed_url = urlparse(url)
		domain = parsed_url.netloc
		domains.add(domain)
	for domain in domains:
		ip=get_ip_address(domain)
		try:
			obj = IPWhois(ip)
			result = obj.lookup_rdap()

			asn_info = result.get('asn', 'ASN information not found')
			asn_Country = result.get('asn_country_code', 'Country not found')
			org = result.get('asn_description', 'Organization not found')
			AS_OrgMap[domain]={"ASN":asn_info,"ORG":org.split(",")[0],"Country":asn_Country}
			print (domain,AS_OrgMap[domain])
		except Exception as e:
			print (str(e))
			time.sleep(2)
	
	return AS_OrgMap

if __name__ == "__main__":
	govtResources=json.load(open("results/resources/govtResources_ZA.json")) #list of govt urls 
	HTTPSupportMap=check_https_support(govtResources)
	AS_OrgMap=get_AS_Org(govtResources)


