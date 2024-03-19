import json
import os
import requests
import time
import sys
from datetime import datetime
import tldextract
import ssl
import csv
from urllib.parse import urlparse
import subprocess


def extract_tld_sld(url):
    extracted = tldextract.extract(url)
    tld = extracted.suffix
    sld = extracted.domain

    full_domain = sld + '.' + tld

    return full_domain

def get_SAN(domain):
	SANList=[]
	try:
		cmd='openssl s_client -connect '+domain+':443 </dev/null 2>/dev/null | openssl x509 -noout -text | grep DNS'
		mycmd=subprocess.getoutput(cmd)
		list=str(mycmd).split(' DNS:')
		for item in list:
			if "unable to load certificate" in item:
				continue
			if not item.isspace():
				SANList.append(item[:-1])
	except Exception as e:
		print ("does not support HTTPS")
	return SANList

def get_domain_extension(url):
    tld_parts = tldextract.extract(url)
    return tld_parts.suffix

def classifyGovtURLs(country,landingsites,allURLs):
	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current Start Time =", current_time) 

	validDomainExtensions=["gov","fed","mil","gouv","gob","go","gub","govern","government","guv","govt","admin"]

	try:
		landingSiteMap=json.load(open("results/resources/landingSiteHeuristics_" + country + ".json"))
	except:
		landingSiteMap={}

	done,SANLists,w_tlds,domainextensions,govtResources,non_govtResources=0,[],set(),set(),set(),set()

	internalURLs=allURLs-landingsites

	print (f"Country: {country} landingsites: {len(landingsites)} internalURLs: {len(internalURLs)} allURLs: {len(allURLs)}")
	
	for site in landingsites:
		parsed_url = urlparse(site)
		domain = parsed_url.netloc
		if domain not in landingSiteMap:
			landingSiteMap[domain]={}
		try:
			SANList=landingSiteMap[domain]["SANs"]
			if len(SANList)<1:
				SANList=get_SAN(domain,country)
				landingSiteMap[domain]["SANs"]=SANList
		except:
			SANList=get_SAN(domain)
			landingSiteMap[domain]["SANs"]=SANList

		SANLists+=SANList
		govtResources.add(site)
		print (100*done/len(landingsites), "\% done")
		done+=1	

		w_tld=extract_tld_sld(domain)
		w_tlds.add(w_tld)
		landingSiteMap[domain]["w_tld"]=w_tld
		

	with open("results/resources/landingSiteHeuristics_" + country + ".json",'w') as fp:
		json.dump(landingSiteMap,fp,indent=4)

	try:
		sanIdentifiedResources=json.load(open("results/resources/sanIdentifiedResources" + country + ".json"))
	except:
		sanIdentifiedResources={}

	found=False
	for resource in internalURLs:
		for san in SANLists:
			if r_tld in extract_tld_sld(san):
				sanIdentifiedResources[r_tld]=san
				found=True
				break
		if found:
			continue	


	for resource in internalURLs:
		found=0
		ext=get_domain_extension(resource)
		parsed_url = urlparse(resource)
		resourcehostname = parsed_url.netloc
		r_tld=extract_tld_sld(resourcehostname)

		#internal resource has a govt extension
		for validext in validDomainExtensions:
			if ext in validext or validext in ext:
				govtResources.add(resource)
				found=1
				break

		if found==1:
			continue

		#domain of the resource matches the landing site's domain
		if resourcehostname in landingSiteMap:
			govtResources.add(resource)
			continue
		if r_tld in w_tlds:
			govtResources.add(resource)
			continue  

		#domain of the resource found in the SANList of the landing sites
		if r_tld in sanIdentifiedResources:
			govtResources.add(resource)
			continue
		non_govtResources.add(resource)
	
	with open("results/resources/non-govtResources_" + country + ".json",'w') as fp:
		json.dump(list(non_govtResources),fp,indent=4)

	
	with open("results/resources/govtResources_" + country + ".json",'w') as fp:
		json.dump(list(govtResources),fp,indent=4) 

	with open("results/resources/sanIdentifiedResources" + country + ".json",'w') as fp:
		json.dump(sanIdentifiedResources,fp,indent=4)


	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current End Time =", current_time) 

	#manually validate the domains classified using the SAN check (that is domains in sanIdentifiedResources) and 
	#exclude any that's not a govt domain
	print (f"RESOURCES FOUND USING SANLIST CHECK: {sanIdentifiedResources}") 

if __name__ == "__main__":
	country="US"

	hostnametoResourcesMap=json.load(open('results/resources/hostnametoResourcesMap_'+country+'.json'))
	landingSites=json.load(open('results/resources/resources_0_'+country+'.json'))
			
		
	allurls=set()
	for website in hostnametoResourcesMap:
		allurls.add(website)
		for resource in hostnametoResourcesMap[website]:
			allurls.add(resource)

	internalResources=classifyGovtURLs(country,set(landingSites.keys()),allurls)

	
