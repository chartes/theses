from capitainizer.position import PositionThese

SRC_PATH="../.."
SRC_FOLDERS=[
    ('positions/pos2000','2000'),
    ('positions/pos2001','2001'),
    ('positions/pos2002','2002'),
    ('positions/pos2003','2003'),
    ('positions/pos2004','2004'),
    ('positions/pos2005','2005'),
    ('positions/pos2006','2006'),
    ('positions/pos2007','2007'),
    ('positions/pos2008','2008'),
    ('positions/pos2009','2009'),
    ('positions/pos2010','2010'),
    ('positions/pos2011','2011'),
    ('positions/pos2012','2012'),
    ('positions/pos2013','2013'),
    ('positions/pos2014','2014'),
    ('positions/pos2015','2015')
]

DEST_PATH="../../data"
METADATA = '../../theses.csv'

if __name__ == "__main__":
    pt = PositionThese(SRC_PATH, METADATA,
                       'templates/__cts__textgroup.xml',
                       'templates/__cts__work.xml',
                       'templates/edition.xml',
                       'templates/refs_decl.xml')

    for folder_name, year in SRC_FOLDERS:
        if pt.write_textgroup(year, DEST_PATH):
            #if pt.write_work(folder_name, year, DEST_PATH):
            #    pt.write_edition(folder_name, year, SRC_PATH, DEST_PATH)

            # from_scratch = False : se base sur les fichiers decapitainisés
            if pt.write_work(folder_name, year, DEST_PATH, from_scratch=False):
                pt.add_refs_decl(folder_name, year, SRC_PATH, DEST_PATH)
