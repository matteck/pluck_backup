#!/opt/homebrew/bin/python3


import requests
import re
import csv
import sys
import requests
import os

DIR = sys.argv[1] + "-SAVED"

csv_filename = sys.argv[1] + ".csv"

with open(csv_filename, newline='') as csvfile:
    csvreader = csv.reader(csvfile, dialect='excel')
    for row in csvreader:
        url = row[3]
        savefile = DIR + "/" + url.split('/')[-1]
        if os.path.isfile(savefile):
            r = requests.head(url, allow_redirects=True)
            online_size = r.headers['content-length']
            file_size = os.path.getsize(savefile)
            if int(online_size) == file_size:
                continue
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 200:
            open(savefile, 'wb').write(r.content)
        else:
            print("Failed %s" % url)
