#!/opt/homebrew/bin/python3

# TO DO
#   - get photos with original download link
#   - 
import requests
import re
import csv
import sys

pluck_csv_file = open("pluck.csv", 'w')
pluck_csv = csv.writer(pluck_csv_file, dialect='excel')


gallery = re.compile(
    '<a href="http://pluck.abc.net.au/ver1.0/CMW/Photos/ManageApprovedSubmissions\?galleryKey=([^"]+)">([^<]+)</a>', flags=re.M)

item = re.compile(
    '<a href="http://pluck.abc.net.au/ver1.0/CMW/Photos/PhotoDetail\?photoKey=([a-f0-9-]+)&galleryKey=([a-f0-9-]+)&?.*">([^<]+)</a>', flags=re.M)

item_description = re.compile('<textarea\s+id="description".*?>(?:<p>)?(.*?)(?:</p>)?</textarea>', flags=re.M|re.S)

item_owner = re.compile('http://pluck.abc.net.au/ver1.0/CMW/Users/User\?userKey=(?:expired_)?\d+">(.*?)</a>')
item_anon_owner = re.compile('<span>\s*anonymous\s*(Anonymous)\s*</span>')
item_tags = re.compile('<input type="text" id="tags" name="tags" value="(.*?)"\s*/>')
next_gallery_page = re.compile('<a href="(http://pluck.abc.net.au/ver1.0/CMW/Photos/\?itemsPerPage=\d+&nextItemOffset=d+&PagnAction=Next&searchString=)">Next</a>')
next_item_page = re.compile('<a href="(http://pluck.abc.net.au/ver1.0/CMW/Photos/ManageApprovedSubmissions\?galleryKey=[a-f0-9-]+&itemsPerPage=\d+&nextItemOffset=\d+&PagnAction=Next)">Next</a>')

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
gallery_top_urls = [
    'http://pluck.abc.net.au/ver1.0/CMW/Photos/?itemsPerPage=100&nextItemOffset=0&PagnAction=Next&searchString=']

media_type = "photo"

for g_url in gallery_top_urls:
    while g_url:
        r1 = requests.get(g_url, cookies=cookies)
        galleries = gallery.findall(r1.text)
        for g in galleries:
            gallery_id = g[0]
            gallery_name = g[1]
            if re.match('\d+ Photos', gallery_name):
                continue
            url = "http://pluck.abc.net.au/ver1.0/CMW/Photos/ManageApprovedSubmissions?galleryKey=%s&itemsPerPage=100&nextItemOffset=0&PagnAction=Next" % gallery_id
            while url:
                r2 = requests.get(url, cookies=cookies)
                items = item.findall(r2.text)
                for i in items:
                    item_id = i[0]
                    item_title = i[2]
                    item_url = "http://pluck.abc.net.au/ver1.0/CMW/Photos/PhotoDetail?photoKey=%s&galleryKey=%s" % (item_id, gallery_id)
                    r3 = requests.get(item_url, cookies=cookies)
                    description = None
                    owner = None
                    tags = None
                    try:
                        m3 = item_description.search(r3.text)
                        description = m3.group(1)
                    except AttributeError:
                        print("Couldn't get description for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)
                    try:
                        m3 = item_owner.search(r3.text)
                        owner = m3.group(1)
                    except AttributeError:
                        try:
                            m3 = item_anon_owner.search(r3.text)
                            owner = "anonymous"
                        except AttributeError:
                            print("Couldn't get owner for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)
                    try:
                        m3 = item_tags.search(r3.text)
                        tags = m3.group(1)
                    except AttributeError:
                        print("Couldn't get tags for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)
                    pluck_csv.writerow([gallery_id, gallery_name, item_id, item_title, owner, tags, description])
                m2 = next_item_page.search(r2.text)
                if m2:
                    url = m2.group(1)
                else:
                    url = None
            m1 = next_gallery_page.search(r1.text)
            if m1:
                g_url = m1.group(1)
            else:
                g_url = None

            
