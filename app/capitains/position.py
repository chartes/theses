import os
from itertools import chain

import lxml.etree as ET
import copy
import shutil
from datetime import date


class PositionThese:

    def __init__(self, src_path, metadata, textgroup_template, work_template, edition_template):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__metadata = {}
        self.__src_path = src_path
        self.__nsmap = {"ti": 'http://www.tei-c.org/ns/1.0'}

        #remove double quotes then trim
        clean = lambda s: s[1:-1].strip()

        with open(metadata, 'r') as meta:
            for line in meta.readlines()[1::]:
                line = line.split(",")
                line.extend([""]*(13-(len(line)-1))) #fill with empty str. should rather use a default dict
                self.__metadata[line[0]] = {
                    "id" : line[0],
                    "promotion" : line[1],
                    "tri": clean(line[2]),
                    "nom": clean(line[3]),
                    "prenom": clean(line[4]),
                    "sexe": line[5],
                    "titre": clean(line[6]),
                    "notBefore": line[7],
                    "notAfter": line[8],
                    "authorKey": clean(line[9]),
                    "authorRef": clean(line[10]),
                    "ppn_position": line[11],
                    "ppn_these": line[12],
                    "an_these": line[13],
                    "sous_titre": ""
                }

    def stringify(self, node):
        parts = ([node.text] +
                        list(chain((ET.tounicode(c) for c in node.getchildren()))) +
                        [node.tail])
        parts = filter(None, parts)
        return ''.join(parts).strip()

    def src_edition(self, pos_year, tri):
        src_edition_fn = os.path.join(self.__src_path, pos_year, "{0}.xml".format(tri))
        if not os.path.isfile(src_edition_fn):
            #raise FileNotFoundError("src file not found: {0}".format(src_edition_fn))
            return ET.Element("div")

        return ET.parse(src_edition_fn)


    @property
    def __tg_template(self): return ET.parse(self.__tg_template_filename)

    @property
    def __wg_template(self): return ET.parse(self.__w_template_filename)

    @property
    def __e_template(self): return ET.parse(self.__e_template_filename)

    def write_to_file(self, filepath, tree):
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                tree_str = ET.tounicode(tree, pretty_print=True)
                f.write(tree_str)


    def write_textgroup(self, pos_year, dest_path):
        # get a fresh new etree
        template = self.__tg_template
        #TODO title ??

        # Update the URN part : pos -> pos2015
        for textgroup in template.xpath("//ti:textgroup", namespaces=template.getroot().nsmap):
            textgroup.set("urn", textgroup.get("urn") + pos_year)

        # Update the groupe name : Position de thèse -> Position de thèse 2015
        for groupname in template.xpath("//ti:groupname", namespaces=template.getroot().nsmap):
            groupname.text = "{0} {1}".format(groupname.text, pos_year)

        # write files
        tg_dirname = os.path.join(dest_path, textgroup.get("urn").split(':')[-1])
        if not os.path.isdir(tg_dirname):
            os.makedirs(tg_dirname)

        self.write_to_file(os.path.join(tg_dirname, "__cts__.xml"), template)

    def write_work(self, pos_year, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            # get a fresh new etree
            template = self.__wg_template

            # Update the URN parts : pos -> pos2015
            for work in template.xpath("//ti:work", namespaces=template.getroot().nsmap):
                work.set("urn", "{0}{1}.pos{2}".format(work.get('urn'), pos_year, meta["id"]))
                work.set("groupUrn", "{0}{1}".format(work.get('groupUrn'), pos_year))

            # title
            src_edition = self.src_edition(pos_year, meta["tri"])
            titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsmap)
            for title in template.xpath("//ti:title", namespaces=template.getroot().nsmap):
                if len(titles) > 0:
                    title.text = self.stringify(titles[0])

            # urn & workUrn
            for edition in template.xpath("//ti:edition", namespaces=template.getroot().nsmap):
                edition.set("workUrn", work.get("urn"))
                edition.set("urn", "{0}.{1}".format(work.get("urn"), "positionThese-fr1"))

            # work label & description
            for label in template.xpath("//ti:edition/ti:label", namespaces=template.getroot().nsmap):
                label.text = self.stringify(titles[0])
            if len(titles) > 1:
                for description in template.xpath("//ti:edition/ti:description", namespaces=template.getroot().nsmap):
                    description.text = self.stringify(titles[1])

            # make workgroup dir
            w_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))
            if os.path.isdir(w_dirname):
                shutil.rmtree(w_dirname)
            os.makedirs(w_dirname)

            self.write_to_file(os.path.join(w_dirname, "__cts__.xml"), template)


    def write_edition(self, pos_year, src_path, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            # get a fresh new etree
            template = self.__e_template

            e_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))

            e_filepath = os.path.join(e_dirname, "{0}.{1}.{2}".format(
                "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]), "positionThese-fr1.xml"
            ))

            src_edition = self.src_edition(pos_year, meta["tri"])

            def insert_into(keyword, struct):
                for tag in template.xpath("//ti:body//ti:div[@type='{0}']".format(keyword), namespaces=self.__nsmap):
                    for c in struct.getchildren():
                        tag.append(copy.deepcopy(c))

            titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsmap)
            # titles
            for title in template.xpath("//ti:teiHeader//ti:titleStmt//ti:title", namespaces=self.__nsmap):
                if title.get("type") == "main" and len(titles) > 0:
                    title.text = self.stringify(titles[0])
                elif title.get("type") == "sub" and len(titles) > 1:
                    title.text = self.stringify(titles[1])

            # author : en attendant meta["authorKey"] et meta["authorRef"]
            for auth in template.xpath("//ti:teiHeader//ti:author", namespaces=self.__nsmap):
                auth.set("key", "{0}, {1}".format(meta["nom"], meta["prenom"]))
                auth.text = "{1} {0}".format(meta["nom"], meta["prenom"])

            # publicationStmt
            for pub_date in template.xpath("//ti:teiHeader//ti:publicationStmt/ti:date", namespaces=self.__nsmap):
                pub_date.set("when", meta["promotion"])

            # profileDesc
            for pub_date in template.xpath("//ti:teiHeader//ti:profileDesc/ti:creation/ti:date", namespaces=self.__nsmap):
                pub_date.set("when", str(date.today().year))

            # année de la promotion dans le titre de la bibliographie
            for bibl_title in template.xpath("//ti:teiHeader//ti:sourceDesc/ti:bibl/ti:title", namespaces=self.__nsmap):
                bibl_title.text = bibl_title.text.replace("@PLACE_HOLDER@", meta["promotion"])

            # front
            front = src_edition.xpath("//ti:front//ti:div", namespaces=self.__nsmap)
            if len(front) > 0:
                insert_into('introduction', front[0])
                if len(front) > 1:
                    insert_into('sources', front[1])

            # body
            for body in template.xpath("//ti:body", namespaces=self.__nsmap):
                body.set("n", "urn:cts:frenchLit:pos{0}.pos{1}.positionThese-fr1".format(meta["promotion"], meta["id"]))

            # parts
            for body in template.xpath("//ti:body/ti:div[@n='2']", namespaces=self.__nsmap):
                for part_id, part in enumerate(src_edition.xpath("//ti:body/ti:div", namespaces=self.__nsmap)):
                    new_part = ET.fromstring("<div n='{0}' type='part'></div>".format(part_id+1))
                    for c in part.getchildren():
                        new_part.append(copy.deepcopy(c))
                    body.append(new_part)

            # back
            back = src_edition.xpath("//ti:back//ti:div", namespaces=self.__nsmap)
            if len(back) > 0:
                insert_into('conclusion', back[0])
                if len(back) > 1:
                    insert_into('appendix', back[1])

            # write the edition file
            self.write_to_file(e_filepath, template)


