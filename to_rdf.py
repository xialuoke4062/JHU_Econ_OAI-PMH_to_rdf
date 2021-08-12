#!/usr/bin/env python
from sickle import Sickle
from pathlib import Path
from sys import argv
import os
import time

def add_entry(key, data_dict, file, field):
    if key in data_dict:
        for elem in data_dict[key]:
            file.write(field + elem + '\n')

def to_rdf(argv):
    var = "append"
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
    URL = 'https://jscholarship.library.jhu.edu/oai/request?set=col_1774.2_34121'
    URL = 'https://jscholarship.library.jhu.edu/oai/request?set=col_1774.2_40418'
    dst_file = '/Users/apple/Dropbox/JHU_Econ_OAI-PMH_to_rdf/result.rdf'   ## In case cron job needs absolute address
    # dst_file = './result.rdf'
    dst_titles = []

    ### Retrieving all records from specific community or collection
    sickle = Sickle(URL)
    records = sickle.ListRecords(metadataPrefix='oai_dc')

    ### Creating brand new rdf file, overriding previous file if already exists
    if var == "override" or not Path(dst_file).exists():
        file = open(dst_file, 'w')
    ### Only append entires with titles that are not in the rdf file
    elif var == "append":
        read_file = open(dst_file, 'r')
        for line in read_file:
            if line[:7] == "Title: ":
                dst_titles.append(line[7:].rstrip())
        read_file.close()
        file = open(dst_file, 'a')
    else:
        return

    ### translating each paper entry into rdf entries
    for record in records:
        data_dict = record.metadata
        ### Remove all None values
        for key, value in data_dict.items():
            data_dict[key] = [x for x in value if x is not None]
        print(data_dict)

        ### Skip existing articles based on title, assuming there will
        ### never be changes to the entries
        if var == "append" and Path(dst_file).exists():
            if data_dict['title'][0] in dst_titles:
                print('Skipping existing article: ' + data_dict['title'][0])    # Debug purpose
                continue
        print('Recording new article: ' + data_dict['title'][0])    # Debug purpose

        # 1. Template-type
        file.write('Template-type: ReDIF-Paper 1.0\n')
        # 2. Author-Name
        add_entry('creator', data_dict, file, "Author-Name: ")
        # 3. Author-Email: not provided on JHU library
        # 4. AUthor-Homepage: not provided on JHU library
        # 5. Author-Workplace-Name: not provided on JHU library
        # 6. Author-Workplace-Homepage: not provided on JHU library
        # 7. Title
        add_entry('title', data_dict, file, "Title: ")
        # 8. Abstract
        add_entry('description', data_dict, file, "Abstract: ")
        # 9. Classification-JELL: Invalid value 'JEL Classification' of type <jel> (attribute 'classification-jel', eval)
        # 10. Keywords
        if 'subject' in data_dict:
            file.write("Keywords: " + ", ".join(data_dict['subject']) + '\n')
        # 11. Note
        # 12. Length: pages
        # 13. Creation-Date: yyyy-mm-dd
        if 'date' in data_dict:
            file.write("Creation-Date: " + data_dict['date'][0][:10] + '\n')
        # 14. Revision-Date: yyyy-mm-dd: difficult to specify
        # 15. Number
        # 16. Publication-Status: Start value with 'Published' or 'Forthcoming'
        # 17. Price
        # 18. File-URL
        if 'identifier' in data_dict:
            file.write("File-URL: " + data_dict['identifier'][0] + '\n')
        # 19. File-Format
        # 20. File-Restriction
        # 21. File-Function
        # 22. File-Size
        # 23. Handle: RePEc:aaa:ssssss: Required but don't have information
        if 'identifier' in data_dict:
            sample_str = str(data_dict['identifier'][0])
            # Get last 5 character
            hdl = sample_str[-5:]
            file.write("Handle: RePEc:jhu:papers:" + hdl + '\n')
        file.write('\n')
    file.close()

if __name__ == "__main__":
    to_rdf(argv)