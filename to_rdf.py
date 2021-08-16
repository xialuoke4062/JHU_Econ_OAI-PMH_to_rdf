#!/usr/bin/env python
from sickle import Sickle
from pathlib import Path
from sys import argv
from bs4 import BeautifulSoup
import os
import time 
import requests

def get_jhu():
    jhu_faculty, jhu_grads = [], []

    ### Faculty Retrieval
    faculty_URL = "https://econ.jhu.edu/people/faculty/"
    resp = requests.get(faculty_URL)
    soupy = BeautifulSoup(resp.content, 'lxml')
    for heading in soupy.find_all(["h3"]):
        name = heading.text.strip()
        jhu_faculty.append(name)

    ### Faculty Retrieval
    grads_URL = "https://econ.jhu.edu/people/graduate-students/"
    resp = requests.get(grads_URL)
    soupy = BeautifulSoup(resp.content, 'lxml')
    for heading in soupy.find_all('tr'):
        cols = heading.find_all('td')
        for col in cols:
            if col.has_attr('class') and col['class'][0] == 'column-1':
                name = col.text.strip().split("\n")[0].strip()
                if name == "Name": continue
                jhu_grads.append(name)

    return jhu_faculty + jhu_grads

def is_jhu(name, jhu_people):
    last_name, first_name = name.split(', ')[0], name.split(', ')[1]
    for person in jhu_people:
        if last_name in person.split() and first_name in person.split():
            return True
    return False

def add_entry(metatags, file, field):
    for taglia in metatags:
        elem = taglia.text
        if elem=="":
            return
        file.write(field + elem + '\n')

def to_rdf(argv):
    ### !!! YOU MAY CHANGE THE DEFAULT EDITING METHOD (override/append)!!!
    var = "override"
    ### !!! YOU MAY CHANGE THE DEFAULT EDITING METHOD (override/append)!!!
    if len(argv) != 1 and len(argv) != 2:
        print("Wrong argument length. Please leave blank (append) or enter override")
        return 
    if len(argv) == 2:
        var = argv[1]
    if var != "append" and var != "override":
        print("Wrong 2nd argument. Please leave blank (append) or enter override")

    ### col_1774.2_64315 is Economics, Department of / Economics Working Paper Archive
    ### col_1774.2_34121 is Biomedical Engineering, Dept. of / Economic Health Care Technologies Design
    URL = 'https://jscholarship.library.jhu.edu/oai/request?set=col_1774.2_64315'
    # URL = 'https://jscholarship.library.jhu.edu/oai/request?set=col_1774.2_34121'
    # URL = 'https://jscholarship.library.jhu.edu/oai/request?set=col_1774.2_40418'
    dst_file = '/Users/apple/Dropbox/JHU_Econ_OAI-PMH_to_rdf/result.rdf'   ## In case cron job needs absolute address
    # dst_file = '//shiner.win.ad.jhu.edu/repec/result_20210813_raw.rdf' # Connect to VPN. map drive "\\shine.win.ad.jhu.edu\repec" on Windows invert backlash for Mac. 
    # dst_file = './result.rdf'
    jhu_people = get_jhu()
    dst_ids = []

    ### Retrieving all records from specific community or collection
    sickle = Sickle(URL)
    # records = sickle.ListRecords(metadataPrefix='oai_dc')
    records = sickle.ListRecords(metadataPrefix='dim')

    ### Creating brand new rdf file, overriding previous file if already exists
    if var == "override" or not Path(dst_file).exists():
        file = open(dst_file, 'w')
    ### Only append entires with titles that are not in the rdf file
    elif var == "append":
        read_file = open(dst_file, 'r')
        for line in read_file:
            if line[:25] == "Handle: RePEc:jhu:papers:":
                dst_ids.append(line[25:].rstrip())
        read_file.close()
        file = open(dst_file, 'a')
    else:
        return

    ### translating each paper entry into rdf entries
    for record in records:
        soupy = BeautifulSoup(record.raw, 'lxml')

        ### Get current record's ID
        metatags = soupy.find_all(attrs={'element':'identifier', 'qualifier':'uri'})
        for taglia in metatags:
            if taglia.text=="":
                break
            id = taglia.text[-5:]

        ### Skip existing articles based on ID
        if var == "append" and Path(dst_file).exists():
            if id in dst_ids:
                print('Skipping existing article: ' + id)    # Debug purpose
                continue
        print('Recording new article: ' + id)    # Debug purpose

        # 1. Template-type
        file.write('Template-type: ReDIF-Paper 1.0\n')
        # 2. Author-Name
        metatags = soupy.find_all(attrs={'element':'contributor', 'qualifier':'author'})
        for taglia in metatags:
            elem = taglia.text
            if elem=="":
                return
            file.write("Author-Name: " + elem + '\n')
            if is_jhu(elem, jhu_people):
                file.write("Author-Workplace-Name: Johns Hopkins University, Department of Economics\n")
        # 3. Author-Email: not provided on JHU library
        # 4. AUthor-Homepage: not provided on JHU library
        # 5. Author-Workplace-Name: written above
        # 6. Author-Workplace-Homepage: not provided on JHU library
        # 7. Title
        metatags = soupy.find_all(attrs={'element':'title'})
        add_entry(metatags, file, "Title: ")
        # 8. Abstract
        metatags = soupy.find_all(attrs={'element':'description', 'qualifier':'abstract'})
        add_entry(metatags, file, "Abstract: ")
        # 9. Classification-JEL
        metatags = soupy.find_all(attrs={'element':'subject', 'qualifier':'jel'})
        jels = []
        for taglia in metatags:
            elem = taglia.text
            if elem=="": break
            jels.append(elem)
        if len(jels) != 0:
            file.write("Classification-JEL: " + ", ".join(jels) + '\n')
        # 10. Keywords
        metatags = soupy.find_all(attrs={'element':'subject'})
        keywords = []
        for taglia in metatags:
            elem = taglia.text
            if elem in jels: continue
            if elem=="": break
            keywords.append(elem)
        if len(keywords) != 0:
            file.write("Keywords: " + ", ".join(keywords) + '\n')
        # 11. Note
        # 12. Length: pages
        # 13. Creation-Date: yyyy-mm-dd
        metatags = soupy.find_all(attrs={'element':'date', 'qualifier':'issued'})
        add_entry(metatags, file, "Creation-Date: ")
        # 14. Revision-Date: yyyy-mm-dd: difficult to specify
        metatags = soupy.find_all(attrs={'element':'date', 'qualifier':'modified'})
        add_entry(metatags, file, "Revision-Date: ")
        # 15. Number
        # 16. Publication-Status: Start value with 'Published' or 'Forthcoming'
        # 17. Price
        # 18. File-URL
        metatags = soupy.find_all(attrs={'element':'identifier', 'qualifier':'uri'})
        add_entry(metatags, file, "File-URL: ")
        # 19. File-Format
        # 20. File-Restriction
        # 21. File-Function
        # 22. File-Size
        # 23. Handle: RePEc:aaa:ssssss: Required but don't have information
        file.write("Handle: RePEc:jhu:papers:" + id + '\n')
        file.write('\n')
    file.close()

if __name__ == "__main__":
    to_rdf(argv)