#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import schema

OSM_PATH = "Tallahassee.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
number = re.compile(r'^[0-9]*$')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']
mapping = { "St": "Street", "Ave": "Avenue",
            "Blvd": "Boulevard", "Dr": "Drive", "Ct": "Court", "Plc": "Place",
            "Sq": "Square", "Ln": "Lane", "Rd": "Road", "Tr": "Trail",
            "Pky": "Parkway", "Pkwy": "Parkway", "N": "North", "S": "South",
            "E": "East", "W": "West", "NW": "Northwest", "NE": "Northeast",
            "SW": "Southwest", "SE": "Southeast",  "Jr": "Junior",
            "Sr": "Senior",  "t": "Capital Circle Southeast", "Hwy":                "Highway"}


def audit_tag(etag, elid):
    audict = {}
    key = etag.get("k")
    value = etag.get("v")
    ttype = "regular"
    if ":" in key:
        ttype, key = key.split(":", 1)
    if "_" in value:
        value = value.replace("_", " ")
    if "_" in key:
        key = key.replace("_", " ")
    if key == "phone":
        tempv = ""
        if value[0] == "1":
            value = value[1:]
        elif value[0] == "+":
            value = value[2:]
        for lett in value:
            if upper.search(lett):
                tempv += lett
        value = tempv
        ttype = "addr"
    if key == "street":
        stname = value.split(" ")
        fixed_list = []
        for word in stname:
            if word in mapping.keys():
                    fixed_list.append(mapping[word])
            elif word[:-1] in mapping.keys():
                    fixed_list.append(mapping[word[:-1]])
            else:
                fixed_list.append(word)
        spc = " "
        value = spc.join(fixed_list)
        ttype = "addr"
    audict["id"] = elid
    audict["key"] = key
    audict["type"] = ttype
    audict["value"] = value
    return audict



def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    # YOUR CODE HERE
    int_list = ['id', 'uid', 'changeset']
    flt_list = ['lat', 'lon']
    if element.tag == "node":
        for attr in element.items():
            if attr[0] in int_list:
                node_attribs[attr[0]] = int(attr[1])
            elif attr[0] in flt_list:
                node_attribs[attr[0]] = float(attr[1])
            elif attr[0] in NODE_FIELDS:
                node_attribs[attr[0]] = attr[1]
    if element.tag == "way":
        poscount = 0
        for attr in element.items():
            if attr[0] in int_list:
                way_attribs[attr[0]] = int(attr[1])
            elif attr[0] in WAY_FIELDS:
                way_attribs[attr[0]] = attr[1]
        for ntag in element.findall("nd"):
            ndict = {}
            ndict["id"] = int(element.get("id"))
            ndict["node_id"] = ntag.get("ref")
            ndict["position"] = poscount
            poscount += 1
            way_nodes.append(ndict)
    for etag in element.findall("tag"):
        elid = int(element.get("id"))
        tdict = audit_tag(etag, elid)
        tags.append(tdict)
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

#    for element in get_element(file_in, tags=('node', 'way')):
#        el = shape_element(element)
    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'wb') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

#        nodes_writer.writeheader()
#        node_tags_writer.writeheader()
#        ways_writer.writeheader()
#        way_nodes_writer.writeheader()
#        way_tags_writer.writeheader()

#        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
#                if validate is True:
#                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
