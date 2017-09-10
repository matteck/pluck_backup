#!/opt/homebrew/bin/python3


import requests
import re
import csv
import sys
import requests
import os
import boto3

debug = True

domain = sys.argv[1]
media_type = sys.argv[2]

assert(domain == "pluck" or domain == "pluck2")
assert(media_type == "Photo" or media_type == "Video" or media_type == "Blog")


csv_filename = "%s-%ss.csv" % (domain, media_type)
logfilename = "%s-%ss-download.log" % (domain, media_type)

logfile = open(logfilename, 'a')

s3 = boto3.resource('s3')
bucket = s3.Bucket('pluck-export')
objects = bucket.objects.filter(Prefix='%s/%s' % (domain, media_type))
size = {}
for o in objects:
    size[o.key] = o.size

with open(csv_filename, 'r') as csvfile:
    csvreader = csv.reader(csvfile, dialect='excel')
    for row in csvreader:
        url = row[3]
        if (url == ''):
            continue
        gallery_id = row[0]
        item_id = row[2]
        filename = url.split('/')[-1]
        # Check if it has two extensions
        if filename[-4:] == '.flv' and filename[-8:-7] == '.':
            filename = filename[0:-4]
        keyname = '%s/%s/%s/%s' % (domain, media_type, gallery_id, filename)
        if keyname in size:
            r = requests.head(url, allow_redirects=True)
            online_size = r.headers['content-length']
            if int(online_size) == size[keyname]:
                if debug:
                    print("Skipping %s size %s" % (keyname, online_size))
                continue
        if debug:
            print("Getting %s" % keyname)
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 200:
            o = bucket.put_object(Key=keyname, Body=r.content)
        else:
            print("%s %s" % (r.status_code, url), file=logfile)