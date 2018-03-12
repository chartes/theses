import csv
import os
from collections import defaultdict
from itertools import chain

import lxml.etree as ET
import copy
import shutil
from datetime import date

CTS_NS = "http://chs.harvard.edu/xmlns/cts"
XML_NS = "http://www.w3.org/XML/1998/namespace"


class PositionThese:

    def __init__(self, src_path, metadata, textgroup_template, work_template, edition_template):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__metadata = defaultdict(str)
        self.__src_path = src_path
        self.__nsmap = {"ti": 'http://www.tei-c.org/ns/1.0'}

        with open(metadata, 'r', newline='') as meta:
            reader = csv.DictReader(meta, delimiter=',', quotechar='"', dialect="unix")
            for line in reader:
                self.__metadata[line["id"]] = line


    @staticmethod
    def stringify(node):
        parts = ([node.text] +
                 list(chain((ET.tounicode(c) for c in node.getchildren()))) +
                 [node.tail])
        parts = filter(None, parts)
        return ''.join(parts).strip()

    def src_edition(self, pos_year, tri):
        src_edition_fn = os.path.join(self.__src_path, pos_year, "{0}.xml".format(tri))
        if not os.path.isfile(src_edition_fn):
            return ET.Element("div")
        return ET.parse(src_edition_fn)

    @property
    def __tg_template(self):
        return ET.parse(self.__tg_template_filename)

    @property
    def __wg_template(self):
        return ET.parse(self.__w_template_filename)

    @property
    def __e_template(self):
        return ET.parse(self.__e_template_filename)

    def write_to_file(self, filepath, tree):
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                tree_str = ET.tounicode(tree, pretty_print=True)
                f.write(tree_str)

    def write_textgroup(self, pos_year, dest_path):
        # get a fresh new etree
        template = self.__tg_template
        # Update the URN part : pos -> pos2015
        textgroup = template.xpath("//ti:textgroup", namespaces=template.getroot().nsmap)

        if textgroup is None:
            raise ValueError('No textgroup detected in the textgroup template document')
        else:
            textgroup[0].set("urn", textgroup[0].get("urn") + pos_year)
            # Update the groupe name : Position de thèse -> Position de thèse 2015
            groupname = template.xpath("//ti:groupname", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0} {1}".format(groupname[0].text, pos_year)

            year = template.xpath("//ti:textgroup//dc:date", namespaces=template.getroot().nsmap)
            year[0].text=pos_year

            # write files
            tg_dirname = os.path.join(dest_path, textgroup[0].get("urn").split(':')[-1])
            if not os.path.isdir(tg_dirname):
                os.makedirs(tg_dirname)

            self.write_to_file(os.path.join(tg_dirname, "__cts__.xml"), template)
            return True

    def encapsulate(self, tag, node, ns):
        return ET.fromstring("<ti:{0} xmlns:ti='{1}' xml:lang='fr'>{2}</ti:{0}>".format(
            tag, ns, self.stringify(node))
        )

    def write_work(self, pos_year, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == str(pos_year)]:
            # get a fresh new etree
            template = self.__wg_template

            # Update the URN parts : pos -> pos2015
            work = template.xpath("//ti:work", namespaces=template.getroot().nsmap)[0]

            year = template.xpath("//ti:work//dc:date", namespaces=template.getroot().nsmap)
            year[0].text=pos_year

            creator = template.xpath("//ti:work//dc:creator", namespaces=template.getroot().nsmap)
            creator[0].text = "{0}, {1}".format(meta["nom"], meta["prenom"])

            is_version_of = template.xpath("//ti:work//dct:relation", namespaces=template.getroot().nsmap)
            is_version_of[0].text = is_version_of[0].text + meta["ppn_these"]

            if work is None:
                raise ValueError('No work detected in the work template document')
            else:
                work.set("urn", "{0}{1}.pos{2}".format(work.get('urn'), pos_year, meta["id"]))
                work.set("groupUrn", "{0}{1}".format(work.get('groupUrn'), pos_year))

                # title
                src_edition = self.src_edition(pos_year, meta["tri"])
                titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsmap)

                template.getroot().insert(0, self.encapsulate("title", titles[0], CTS_NS))

                # urn & workUrn
                edition = template.xpath("//ti:edition", namespaces=template.getroot().nsmap)[0]
                edition.set("workUrn", work.get("urn"))
                edition.set("urn", "{0}.{1}".format(work.get("urn"), "positionThese-fr1"))
                # work label & description
                edition.insert(0, self.encapsulate("label", titles[0], CTS_NS))
                if len(titles) > 1:
                    edition.insert(1, self.encapsulate("description", titles[1], CTS_NS))

                # make workgroup dir
                w_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))
                if os.path.isdir(w_dirname):
                    shutil.rmtree(w_dirname)
                os.makedirs(w_dirname)
                self.write_to_file(os.path.join(w_dirname, "__cts__.xml"), template)

        return True

    def write_edition(self, pos_year, src_path, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            # get a fresh new etree
            template = self.__e_template

            e_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))

            e_filepath = os.path.join(e_dirname, "{0}.{1}.{2}".format(
                "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]), "positionThese-fr1.xml"
            ))

            src_edition = self.src_edition(pos_year, meta["tri"])

            root = template.getroot()
            root.set("{0}id".format("{" + XML_NS + "}"), "position-{0}".format(meta["id"]))

            # titles
            titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsmap)
            titleStmt = template.xpath("//ti:teiHeader//ti:titleStmt", namespaces=self.__nsmap)
            if len(titles) > 0:
                t = self.encapsulate("title", titles[0], self.__nsmap["ti"])
                t.set('type', 'main')
                titleStmt[0].insert(0, t)
            if len(titles) > 1:
                sub_title = self.encapsulate("title", titles[1], self.__nsmap["ti"])
                sub_title.set('type', 'sub')
                titleStmt[0].insert(1, sub_title)

            auth = template.xpath("//ti:teiHeader//ti:author", namespaces=self.__nsmap)
            auth[0].set("key", meta["authorKey"])
            auth[0].set("ref", meta["authorRef"])
            auth[0].text = "{1} {0}".format(meta["nom"], meta["prenom"])

            # publicationStmt
            pub_date = template.xpath("//ti:teiHeader//ti:publicationStmt/ti:date", namespaces=self.__nsmap)
            pub_date[0].set("when", meta["promotion"])

            # profileDesc
            crea_date = template.xpath("//ti:teiHeader//ti:profileDesc/ti:creation/ti:date", namespaces=self.__nsmap)
            crea_date[0].set("when", str(date.today().year))

            # année de la promotion dans le titre de la bibliographie
            bibl_title = template.xpath("//ti:teiHeader//ti:sourceDesc/ti:bibl/ti:title", namespaces=self.__nsmap)
            bibl_title[0].text = bibl_title[0].text.replace("PLACE_HOLDER", meta["promotion"])

            def insert_into(keyword, struct):
                for tag in template.xpath("//ti:body//ti:div[@type='{0}']".format(keyword), namespaces=self.__nsmap):
                    for c in struct.getchildren():
                        tag.append(copy.deepcopy(c))
                return tag

            part_index = 1
            # front
            front = src_edition.xpath("//ti:front//ti:div", namespaces=self.__nsmap)
            if len(front) > 0:
                intro = insert_into('introduction', front[0])
                intro.set("n", str(part_index))
                part_index += 1
                if len(front) > 1:
                    sources = insert_into('sources', front[1])
                    sources.set("n", str(part_index))
                    part_index += 1

            # body
            body = template.xpath("//ti:body", namespaces=self.__nsmap)
            body[0].set("n", "urn:cts:frenchLit:pos{0}.pos{1}.positionThese-fr1".format(meta["promotion"], meta["id"]))

            # parts
            parts = src_edition.xpath("//ti:body/ti:div", namespaces=self.__nsmap)
            for i, part in enumerate(parts):
                new_part = ET.fromstring("<div n='{0}' type='part'></div>".format(part_index))
                for j, c in enumerate(part.getchildren()):
                    sec = copy.deepcopy(c)
                    sec.set("n", str(j))
                    sec.set("type", "chapter")
                    new_part.append(sec)
                body[0].insert(i + 2, new_part)
                part_index += 1

            # back
            back = src_edition.xpath("//ti:back//ti:div", namespaces=self.__nsmap)
            if len(back) > 0:
                conclusion = insert_into('conclusion', back[0])
                conclusion.set("n", str(part_index))
                part_index += 1
                if len(back) > 1:
                    appendix = insert_into('appendix', back[1])
                    appendix.set("n", str(part_index))
                    part_index += 1

            # write the edition file
            self.write_to_file(e_filepath, template)