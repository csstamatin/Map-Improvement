# -*- coding: utf-8 -*-
"""
Created on Fri Nov 11 18:26:00 2016

@author: cssta
"""


import xml.etree.cElementTree as ET
import pprint
import re
"""
This was originaly
"""


lower = re.compile(r'^[a-zA-Z  ]*$')
upper = re.compile(r'^[0-9]* [a-zA-Z0-9  ]*$')
prob = re.compile(r'[=\+/&<>:\(\);\'"\?!|\\\\ ` _\e%#$@\,\.\t\r\n]')


def key_type(element, keys, keycnt, bute):
    if element.tag == "tag":
        elval = element.attrib[bute]
        if lower.search(elval):
            keys["lower"].append(elval)
            keycnt["lower"] += 1
        elif upper.search(elval):
            keys["upper"].append(elval)
            keycnt["upper"] += 1
        elif
        elif prob.search(elval):
            keys["prob"].append(elval)
            #print element.attrib[bute]
            keycnt["prob"] += 1
        else:
            if element.attrib["k"] == "phone":
                tempv = ""
                if elval[0] == "1":
                    elval = elval[1:]
                for lett in elval:
                    if upper.search(lett):
                        tempv += lett
            keys["other"].append(elval)
            #print element.attrib[bute]
            keycnt["other"] += 1
    return keys, keycnt



def process_map(filename):
    keys = {"lower": [], "upper": [], "prob": [], "other": []}
    keycnt = {"lower": 0, "upper": 0, "prob": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys, keycnt = key_type(element, keys, keycnt, "v")

    return keys, keycnt



def test():
    keys, keycnt = process_map('Tallahassee.osm')
    pprint.pprint(keycnt)

#    pprint.pprint(keys["upper"][:100])
#    pprint.pprint(keys["prob"][2000:2050])
#    pprint.pprint(keys["other"])
#    assert keys == {'lower': 5, 'lower_colon': 0, 'other': 1, 'problemchars': 1}


if __name__ == "__main__":
    test()