#!/opt/homebrew/bin/python3

# TO DO
#   - get photos with original download link
#   - 
import requests
import re
import csv
import sys

debug = False

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

pluck_csv_file = open("%s-%ss.csv" % (domain, media_type), 'w')
pluck_csv = csv.writer(pluck_csv_file, dialect='excel')

gallery_regex = re.compile(
    '<a href="http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=([^"]+)">([^<]+)</a>' % (domain,media_type), flags=re.M|re.I)
item_regex = re.compile(
    '<a href="http://%s.abc.net.au/ver1.0/CMW/%ss/%sDetail\?[^"]*%sKey=([a-f0-9-]+)[^"]*">([^<]+)</a>' % (domain, media_type, media_type, media_type), flags=re.M|re.I)
item_description_regex = re.compile('<textarea\s+id="description".*?>(.*?)</textarea>', flags=re.M|re.S)
item_owner_regex = re.compile('http://%s.abc.net.au/ver1.0/CMW/Users/User\?userKey=(?:expired_)?\d+">(.*?)</a>' % (domain))
item_anon_owner_regex = re.compile('<span>\s*anonymous\s*(Anonymous)\s*</span>')
item_tags_regex = re.compile('<input type="text" id="tags" name="tags" value="(.*?)"\s*/>', flags=re.M|re.S)
next_gallery_page_regex = re.compile('<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/\?itemsPerPage=\d+&nextItemOffset=d+&PagnAction=Next&searchString=)">Next</a>' % (domain,media_type), flags=re.I)
next_item_page_regex = re.compile('<a href="(http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions\?galleryKey=[a-f0-9-]+&itemsPerPage=\d+&nextItemOffset=\d+&PagnAction=Next)">Next</a>' % (domain,media_type), flags=re.I)

if media_type == "video":
    download_url_regex = re.compile('<a href="(http://%s.abc.net.au/ver1.0/Content/Videos/Store/Main/[a-f0-9-]+/[a-f0-9-]+/[a-f0-9-]+(?:\.[^"]+)?)"' % (domain), flags=re.I)
else:
    download_url_regex = re.compile('<a href="(http://%s.abc.net.au/ver1.0/../static/images/store/[a-f0-9-]+/[a-f0-9-]+/[a-f0-9-]+[^"]*)"' % (domain), flags=re.I)    
    

gallery_list_url ='http://%s.abc.net.au/ver1.0/CMW/%ss/?itemsPerPage=100&nextItemOffset=0&PagnAction=Next&searchString=' % (domain, media_type)



while gallery_list_url:
    if debug:
        print(gallery_list_url)
    r1 = requests.get(gallery_list_url, cookies=cookies)
    galleries = gallery_regex.findall(r1.text)
    for g in galleries:
        gallery_id = g[0]
        if gallery_id in ('8d6e331b-0d00-4ed3-94f2-58e26b196a62','b4c68ba3-27d0-4355-a657-ba2d16cc5dd0'):
            continue
        gallery_name = g[1]
        if re.match('\d+ Photos', gallery_name):
            continue
        gallery_url = "http://%s.abc.net.au/ver1.0/CMW/%ss/ManageApprovedSubmissions?galleryKey=%s&itemsPerPage=100&nextItemOffset=0&PagnAction=Next" % (domain, media_type, gallery_id)
        if debug:
            print("Gallery URL: ", gallery_url)
        while gallery_url:
            r2 = requests.get(gallery_url, cookies=cookies)
            items = item_regex.findall(r2.text)
            for i in items:
                item_id = i[0]
                item_title = i[1]
                item_url = "http://%s.abc.net.au/ver1.0/CMW/%ss/%sDetail?%sKey=%s&galleryKey=%s" % (domain, media_type, media_type, media_type, item_id, gallery_id)
                if debug:
                    print(item_url)
                r3 = requests.get(item_url, cookies=cookies)
                description = None
                owner = None
                tags = None
                download_url = None

                try:
                    m3 = item_description_regex.search(r3.text)
                    description = m3.group(1)
                except AttributeError:
                    print("Couldn't get description for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)

                try:
                    m3 = item_owner_regex.search(r3.text)
                    owner = m3.group(1)
                except AttributeError:
                    try:
                        m3 = item_anon_owner_regex.search(r3.text)
                        owner = "anonymous"
                    except AttributeError:
                        print("Couldn't get owner for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)

                try:
                    m3 = item_tags_regex.search(r3.text)
                    tags = m3.group(1)
                except AttributeError:
                    print("Couldn't get tags for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)

                try:
                    m3 = download_url_regex.search(r3.text)
                    download_url = m3.group(1)
                except AttributeError:
                    print("Couldn't get download URL for %s %s in %s" % (media_type, item_id, gallery_id), file=sys.stderr)

                pluck_csv.writerow([gallery_id, gallery_name, item_id, download_url, item_title, owner, tags, description])
            m2 = next_item_page_regex.search(r2.text)
            if m2:
                gallery_url = m2.group(1)
            else:
                gallery_url = None
        m1 = next_gallery_page_regex.search(r1.text)
        if m1:
            gallery_list_url = m1.group(1)
        else:
            gallery_list_url = None