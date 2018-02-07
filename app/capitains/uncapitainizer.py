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


def uncapitanize(dest):
    positions = []

    for folder_name in SRC_FOLDERS:
        edition_path = os.path.join(DEST_PATH, "pos"+folder_name)
        editions = []
        for dirname, dirnames, filenames in os.walk(edition_path):
            for subdirname in dirnames:
                editions.append(os.path.join(dirname, subdirname))

        for e in editions:
            for d, ds, filenames in os.walk(e):
                for fn in filenames:
                    if "positionThese" in fn:
                        pos = os.path.join(e, fn)
                        promotion = e.split("/")[-2]
                        new_name = e.split("/")[-1] + ".xml"
                        positions.append((pos, os.path.join(dest, promotion, new_name)))

    positions.sort()

    for cp, up in positions:
        with open(cp, 'r') as p:
            capitanized_pos = ET.parse(p)
            c = capitanized_pos.xpath("//ti:teiHeader//ti:refsDecl", namespaces={"ti": 'http://www.tei-c.org/ns/1.0'})
            c[0].getparent().remove(c[0])

            directory = "/".join(up.split("/")[0:-1])
            if not os.path.exists(directory):
                os.makedirs(directory)

            with open(up, 'w+') as up:
                tree_str = ET.tounicode(capitanized_pos, pretty_print=True)
                up.write(tree_str)



if __name__ == "__main__":

    uncapitanize("../../positions")

