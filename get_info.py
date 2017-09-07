#!/opt/homebrew/bin/python3

import requests
import re
import csv
import sys
import urllib

debug = True

domain = sys.argv[1]
media_type = sys.argv[2]

print("Doing ", domain, media_type)

cookies = {
    'anonId': '7c16e624-623f-4eab-b671-21c9d3f614f2',
    'SRV_ID': 'usw1web023.aws-us.pluck.com',
    '_ga': 'GA1.3.1441809091.1504500391',
    '_gid': 'GA1.3.1885729025.1504500391',
    'ABCGuestID': '23.50.50.14.247841504500394611',
    '__gads=ID=cf0040a3ba85dd1a:T=1504500427:S': 'ALNI_MZAV8KPwN6-FxRJvU--rA31aBkiMA',
    'AT=u=400328&a=matteck&t=1504536432&e=matt555@mathomat.net&f=Matt&n=Eckhaus&h': 'a6dfb504587c4e2538bb62c433a3aa8b',
    'ABCUSERCENTRALSESSION=Handle=MattEck&SecurityCode=08E12769%2D4A37%2D4D8D%2DA546%2DBBEE762F30EA&REGLOGIN=y&SessionID=10592703&UserClass': 'kids',
    'SiteLifeHost': 'usw1web023aws-uspluckcom',
    'ASP.NET_SessionId': 'bmjojmybeykicjnrcsyftctg',
}

gallery_list_url = 'http://%s.abc.net.au/ver1.0/CMW/%ss/?itemsPerPage=100&nextItemOffset=0&PagnAction=Next&searchString=' % (
    domain, media_type)

gallery_regex = re.compile(
    '<a href="http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=([^"]+)">([^<]+)</a>' % (domain, media_type), flags=re.M | re.I)
item_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/%sDetail\?[^"]*?%sKey=([a-f0-9-]+)[^"]*?)">([^<]+)</a>' % (domain, media_type, media_type, media_type), flags=re.M | re.I)
item_description_regex = re.compile(
    '<textarea\s+id="description".*?>(.*?)</textarea>', flags=re.M | re.S)
item_owner_regex = re.compile(
    'http://%s.abc.net.au/ver1.0/CMW/Users/User\?userKey=(?:expired_)?\d+">(.*?)</a>' % (domain))
item_anon_owner_regex = re.compile(
    '<span>\s*anonymous\s*(Anonymous)\s*</span>')
item_tags_regex = re.compile(
    '<input type="text" id="tags" name="tags" value="(.*?)"\s*/>', flags=re.M | re.S)
next_gallery_page_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/\?itemsPerPage=\d+&nextItemOffset=d+&PagnAction=Next&searchString=)">Next</a>' % (domain, media_type), flags=re.I)
next_item_page_regex = re.compile(
    '<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=[a-f0-9-]+&itemsPerPage=\d+&nextItemOffset=\d+&PagnAction=Next)">Next</a>' % (domain, media_type), flags=re.I)

if media_type == "video":
    download_url_regex = re.compile(
        '<a href="(http://%s.abc.net.au/ver1.0/Content/Videos/Store/Main/[a-f0-9-]+/[a-f0-9-]+/[a-f0-9-]+(?:\.[^"]+)?)"' % (domain), flags=re.I)
else:
    download_url_regex = re.compile(
        '<a href="(http://%s.abc.net.au/ver1.0/../static/images/store/[a-f0-9-]+/[a-f0-9-]+/[a-f0-9-]+[^"]*)"' % (domain), flags=re.I)

csv_filename = "%s-%ss.csv" % (domain, media_type)
log_filename = "%s-%ss.csv" % (domain, media_type)

# Get completed galleries
galleries_done = set()
with open(csv_filename) as csvfile:
    csvreader = csv.reader(csvfile, dialect='excel')
    for row in csvreader:
        gallery_id = row[0]
        galleries_done.add(gallery_id)
if debug:
    print("Skipping completed galleries")
    print(galleries_done)

logfile = open(log_filename, 'w')
csvfile = open(csv_filename, 'a')
pluck_csv = csv.writer(csvfile, dialect='excel')

# Get a list of gallery_ids to do
galleries_todo = {}
while gallery_list_url:
    if debug:
        print(gallery_list_url)
    r = requests.get(gallery_list_url, cookies=cookies)
    galleries = gallery_regex.findall(r.text)
    for g in galleries:
        gallery_id = g[0]
        gallery_name = g[1]
        if re.match('\d+ %ss' % media_type, gallery_name, flags=re.I):
            continue
        galleries_todo[g[0]] = g[1]
        if debug:
            print(gallery_id)
    m = next_gallery_page_regex.search(r.text)
    if m:
        gallery_list_url = m.group(1)
    else:
        gallery_list_url = None

items_todo = {}
for gallery_id in galleries_todo:
    gallery_url = "http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions?galleryKey=%s&itemsPerPage=100&nextItemOffset=0&PagnAction=Next" % (
        domain, media_type, gallery_id)
    while gallery_url:
        if debug:
            print("Gallery URL: ", gallery_url)
        r = requests.get(gallery_url, cookies=cookies)
        items = item_regex.findall(r.text)
        for i in items:
            item_id = i[1]
            item_title = i[2]
            items_todo[item_id] = item_title
        # m = next_item_page_regex.search(r.text)
        # if m:
        #     gallery_url = m.group(1)
        # else:
        #     gallery_url = None
        gallery_url = None

    for item_id in items_todo:

        item_url = 'http://%s.abc.net.au/ver1.0/sdk/js/Pluck-6.0.15?ath=a6dfb504587c4e2538bb62c433a3aa8b&jsonRequest=%%7B%%22Envelopes%%22%%3A%%5B%%7B%%22Payload%%22%%3A%%7B%%22ObjectType%%22%%3A%%22Requests.Media.%sRequest%%22%%2C%%22%sKey%%22%%3A%%7B%%22Key%%22%%3A%%22%s%%22%%2C%%22ObjectType%%22%%3A%%22Models.Media.%sKey%%22%%7D%%7D%%2C%%22PayloadType%%22%%3A%%22Requests.Media.%sRequest%%22%%7D%%5D%%2C%%22Metadata%%22%%3Anull%%2C%%22ObjectType%%22%%3A%%22Requests.RequestBatch%%22%%7D&cb=plcksdk_0&u=67201015' % (domain, media_type, media_type, item_id, media_type, media_type)
        
        r = requests.get(item_url, cookies=cookies)
        if r.status_code != 200:
            print("Couldn't retrieve item page: %s" % item_url, file=log_file)
            continue
        item_data = r.json()
        print(r)
        description = None
        owner = None
        tags = None
        download_url = None
        # try:
        #     m3 = item_description_regex.search(r3.text)
        #     description = m3.group(1)
        # except AttributeError:
        #     print("Couldn't get description for %s %s in %s" % (media_type, item_id, gallery_id), file=log_file)

        #         try:
        #             m3 = item_owner_regex.search(r3.text)
        #             owner = m3.group(1)
        #         except AttributeError:
        #             try:
        #                 m3 = item_anon_owner_regex.search(r3.text)
        #                 owner = "anonymous"
        #             except AttributeError:
        #                 print("Couldn't get owner for %s %s in %s" % (media_type, item_id, gallery_id), file=log_file)

        #         try:
        #             m3 = item_tags_regex.search(r3.text)
        #             tags = m3.group(1)
        #         except AttributeError:
        #             print("Couldn't get tags for %s %s in %s" % (media_type, item_id, gallery_id), file=log_file)

        #         try:
        #             m3 = download_url_regex.search(r3.text)
        #             download_url = m3.group(1)
        #         except AttributeError:
        #             print("Couldn't get download URL for %s %s in %s" % (media_type, item_id, gallery_id), file=log_file)

        #         pluck_csv.writerow([gallery_id, gallery_name, item_id, download_url, item_title, owner, tags, description])
