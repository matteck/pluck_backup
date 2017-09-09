#!/opt/homebrew/bin/python3

import requests
import re
import csv
import sys
import urllib
import json
import os

debug = False

domain = sys.argv[1]
media_type = sys.argv[2]

assert(domain == "pluck" or domain == "pluck2")
assert(media_type == "Photo" or media_type == "Video" or media_type == "Blog")

print("Doing ", domain, media_type)

cookies = {
    'SRV_ID': 'usw1web023.aws-us.pluck.com',
    'AT=u=400328&a=matteck&t=1504536432&e=matt555@mathomat.net&f=Matt&n=Eckhaus&h': 'a6dfb504587c4e2538bb62c433a3aa8b',
    'SiteLifeHost': 'usw1web023aws-uspluckcom',
}

# Regexes for scraping Pluck CMW
gallery_regex = re.compile(
    '<a href="http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=([^"]+)">([^<]+)</a>' % (domain, media_type), flags=re.M | re.I)
item_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/%sDetail\?[^"]*?%sKey=([a-f0-9-]+)[^"]*?)">([^<]+)</a>' % (domain, media_type, media_type, media_type), flags=re.M | re.I)
next_gallery_page_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/\?itemsPerPage=\d+&nextItemOffset=d+&PagnAction=Next&searchString=)">Next</a>' % (domain, media_type), flags=re.I)
next_item_page_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=[a-f0-9-]+&itemsPerPage=\d+&nextItemOffset=\d+&PagnAction=Next)">Next</a>' % (domain, media_type), flags=re.I)

csv_filename = "%s-%ss.csv" % (domain, media_type)
logfilename = "%s-%ss.log" % (domain, media_type)

# Get completed galleries
galleries_done = set()
if os.path.exists(csv_filename):
    with open(csv_filename) as csvfile:
        csvreader = csv.reader(csvfile, dialect='excel')
        for row in csvreader:
            gallery_id = row[0]
            galleries_done.add(gallery_id)
    if debug:
        print("Skipping completed galleries")
        print(galleries_done)

logfile = open(logfilename, 'a')
csvfile = open(csv_filename, 'a')
pluck_csv = csv.writer(csvfile, dialect='excel')

# Get a list of gallery_ids to do
gallery_list_url = 'http://%s.abc.net.au/ver1.0/CMW/%ss/?itemsPerPage=100&nextItemOffset=0&PagnAction=Next&searchString=' % (
    domain, media_type)
galleries_todo = {}
while gallery_list_url:
    if debug:
        print(gallery_list_url)
    r = requests.get(gallery_list_url, cookies=cookies)
    galleries = gallery_regex.findall(r.text)
    for g in galleries:
        gallery_id = g[0]
        gallery_name = g[1]
        # Skip duplicate links
        if re.match('\d+ %ss' % media_type, gallery_name, flags=re.I):
            continue
        if gallery_id in galleries_done:
            print("Skipping %s (done)" % gallery_id)
            continue
        galleries_todo[g[0]] = g[1]
        if debug:
            print(gallery_id)
    m = next_gallery_page_regex.search(r.text)
    if m:
        gallery_list_url = m.group(1)
    else:
        gallery_list_url = None

for gallery_id in galleries_todo:
    items_todo = []
    print("Getting gallery %s..." % gallery_id)
    gallery_url = "http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions?galleryKey=%s&itemsPerPage=100&nextItemOffset=0&PagnAction=Next" % (
        domain, media_type, gallery_id)
    while gallery_url:
        if debug:
            print("Gallery URL: ", gallery_url)
        r = requests.get(gallery_url, cookies=cookies)
        items = item_regex.findall(r.text)
        for i in items:
            item_id = i[1]
            items_todo.append({'item_id': item_id})
        m = next_item_page_regex.search(r.text)
        if m:
            gallery_url = m.group(1)
        else:
            gallery_url = None
        gallery_url = None

    for item in items_todo:
        item_id = item['item_id']
        jsonRequest = {
            "Envelopes": [
                {
                    "Payload": {
                        "ObjectType": "Requests.Media.%sRequest" % media_type,
                        "%sKey" % media_type: {
                            "Key": item_id,
                            "ObjectType": "Models.Media.%sKey" % media_type
                        }
                    },
                    "PayloadType": "Requests.Media.%sRequest" % media_type
                }
            ],
            "Metadata": None,
            "ObjectType": "Requests.RequestBatch"
        }
        jsonRequest = json.dumps(jsonRequest)
        jsonRequest = urllib.parse.quote(jsonRequest)
        item_url = 'http://%s.abc.net.au/ver1.0/sdk/js/Pluck-6.0.15?jsonRequest=%s&cb=plcksdk_0' % (domain, jsonRequest)
        if debug:
            print(item_url)

        r = requests.get(item_url, cookies=cookies)
        if r.status_code != 200:
            print("Status code %s for item %s - " % (r.status_code, item_id, item_url), file=logfile)
            continue
        if r.text == '':
            print("Empty response for item %s - " % (item_id, item_url), file=logfile)
            continue
        try:
            item_data = r.text[10:-2]
            item_data = json.loads(item_data)
            status = item_data['Envelopes'][0]['Payload']['ResponseStatus']['StatusCode']
            assert(status == 'OK')
            item_data = item_data['Envelopes'][0]['Payload'][media_type]
        except:
            print("Couldn't get data for item %s - %s" % (item_id, item_url), file=logfile)
            continue
        for keyword in ('Title', 'Description', 'Tags'):
            try:
                item[keyword] = item_data[keyword]
            except KeyError:
                print("Item %s missing %s - %s" % (item_id, keyword, item_url), file=logfile)
                item[keyword] = ''
        try:
            item['owner'] = item_data['Owner']['DisplayName']
        except KeyError:
            print("Item %s missing owner - %s" % (item_id, item_url), file=logfile)
            item['owner'] = ''
        try:
            if media_type == 'Photo':
                item['download_url'] = item_data['Image']['FullPendingApproval']
            else:
                item['download_url'] = item_data['Video']['Url']
        except KeyError:
            print("Item %s missing download url - %s" % (item_id, item_url), file=logfile)
            item['download_url'] = ''
        item['completed'] = True
    
    print("Writing gallery %s..." % gallery_id)
    for item in items_todo:
        if 'completed' not in item:
            continue
        if debug:
            print(item['item_id'])
        pluck_csv.writerow([gallery_id, gallery_name, item['item_id'], item['download_url'], item['Title'], item['owner'], item['Tags'], item['Description']])
    logfile.flush()
    csvfile.flush()


        # print(json.dumps(items_todo, indent=2, sort_keys=True))
        # sys.exit()
