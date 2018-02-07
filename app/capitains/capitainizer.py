from capitains.capitainizer.position import PositionThese
import lxml.etree as ET

import os

SRC_PATH="../.."
SRC_FOLDERS=[
    '2000',
    '2001',
    '2002',
    '2003',
    '2004',
    '2005',
    '2006',
    '2007',
    '2008',
    '2009',
    '2010',
    '2011',
    '2012',
    '2013',
    '2014',
    '2015'
]

DEST_PATH="../../data"
METADATA = '../../theses.csv'

if __name__ == "__main__":
    pt = PositionThese(SRC_PATH, METADATA,
                       'templates/__cts__textgroup.xml',
                       'templates/__cts__work.xml',
                       'templates/edition.xml')

    for folder_name in SRC_FOLDERS:
        if pt.write_textgroup(folder_name, DEST_PATH):
            if pt.write_work(folder_name, DEST_PATH):
                pt.write_edition(folder_name, SRC_PATH, DEST_PATH)

