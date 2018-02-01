import os
import lxml.etree as ET
import copy
import shutil
from datetime import date

class PositionThese:

    def __init__(self, metadata, textgroup_template, work_template, edition_template):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__metadata = {}

        #remove double quotes then trim
        clean = lambda s: s[1:-1].strip()

        with open(metadata, 'r') as meta:
            for line in meta.readlines()[1::]:
                line = line.split(",")
                line.extend([""]*(13-(len(line)-1)))
                titres = clean(line[6]).split(".")
                self.__metadata[line[0]] = {
                    "id" : line[0],
                    "promotion" : line[1],
                    "tri": clean(line[2]),
                    "nom": clean(line[3]),
                    "prenom": clean(line[4]),
                    "sexe": line[5],
                    "titre": "",
                    "notBefore": line[7],
                    "notAfter": line[8],
                    "authorKey": clean(line[9]),
                    "authorRef": clean(line[10]),
                    "ppn_position": line[11],
                    "ppn_these": line[12],
                    "an_these": line[13],
                    "sous_titre": ""
                }

                # split the subtitle from the title if any
                self.__metadata[line[0]]["titre"] = titres[0].strip()
                if len(titres) > 1:
                    self.__metadata[line[0]]["sous_titre"] = titres[1].strip()

                # print(self.__metadata[line[0]])

    @property
    def __tg_template(self): return ET.parse(self.__tg_template_filename)

    @property
    def __wg_template(self): return ET.parse(self.__w_template_filename)

    @property
    def __e_template(self): return ET.parse(self.__e_template_filename)

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

        tg_filepath = os.path.join(tg_dirname, "__cts__.xml")
        if not os.path.isfile(tg_filepath):
            with open(tg_filepath, 'w') as f:
                cts_tg = ET.tounicode(template, pretty_print=True)
                f.write(cts_tg)
                #print(cts_tg)

    def write_work(self, pos_year, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            # get a fresh new etree
            template = self.__wg_template

            # Update the URN parts : pos -> pos2015
            for work in template.xpath("//ti:work", namespaces=template.getroot().nsmap):
                work.set("urn", "{0}{1}.pos{2}".format(work.get('urn'), pos_year, meta["id"]))
                work.set("groupUrn", "{0}{1}".format(work.get('groupUrn'), pos_year))

            # title
            for title in template.xpath("//ti:title", namespaces=template.getroot().nsmap):
                title.text = meta["titre"]

            # urn & workUrn
            for edition in template.xpath("//ti:edition", namespaces=template.getroot().nsmap):
                edition.set("workUrn", work.get("urn"))
                edition.set("urn", "{0}.{1}".format(work.get("urn"), "positionThese-fr1"))

            # work label & description
            for label in template.xpath("//ti:edition/ti:label", namespaces=template.getroot().nsmap):
                label.text = meta["titre"]

            for description in template.xpath("//ti:edition/ti:description", namespaces=template.getroot().nsmap):
                 description.text = meta["sous_titre"]

            # make workgroup dir
            w_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))
            if os.path.isdir(w_dirname):
                shutil.rmtree(w_dirname)
            #if not os.path.isdir(w_dirname):
            os.makedirs(w_dirname)

            w_filepath = os.path.join(w_dirname, "__cts__.xml")
            if not os.path.isfile(w_filepath):
                with open(w_filepath, 'w') as f:
                    cts_w = ET.tounicode(template, pretty_print=True)
                    f.write(cts_w)
                    #print(cts_w)

    def write_edition(self, pos_year, src_path, dest_path):
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            # get a fresh new etree
            template = self.__e_template

            e_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))

            e_filepath = os.path.join(e_dirname, "{0}.{1}.{2}".format(
                "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]), "positionThese-fr1.xml"
            ))


            src_edition_fn = os.path.join(src_path, pos_year, "{0}.xml".format(meta["tri"]))
            if not os.path.isfile(src_edition_fn):
                raise FileNotFoundError("src file not found: {0}".format(src_edition_fn))

            src_edition = ET.parse(src_edition_fn)
            nsmap = {"ti" : 'http://www.tei-c.org/ns/1.0'}


            def update(keyword, struct):
                for intro in template.xpath("//ti:body//ti:div[@type='{0}']".format(keyword), namespaces=nsmap):
                    for c in struct.getchildren():
                        intro.append(copy.deepcopy(c))

            # titles
            for title in template.xpath("//ti:teiHeader//ti:titleStmt//ti:title", namespaces=nsmap):
                if title.get("type") == "main":
                    title.text = meta["titre"]
                elif title.get("type") == "sub":
                    title.text = meta["sous_titre"]

            # author
            for auth in template.xpath("//ti:teiHeader//ti:author", namespaces=nsmap):
                auth.set("key", "{0}, {1}".format(meta["nom"], meta["prenom"]))
                auth.text = "{1} {0}".format(meta["nom"], meta["prenom"])

            # publicationStmt
            for pub_date in template.xpath("//ti:teiHeader//ti:publicationStmt/ti:date", namespaces=nsmap):
                pub_date.set("when", meta["promotion"])

            # profileDesc
            for pub_date in template.xpath("//ti:teiHeader//ti:profileDesc/ti:creation/ti:date", namespaces=nsmap):
                pub_date.set("when", str(date.today().year))

            # front
            front = src_edition.xpath("//ti:front//ti:div", namespaces=nsmap)
            if len(front) > 0:
                update('introduction', front[0])
                if len(front) > 1:
                    update('sources', front[1])

            # body
            for body in template.xpath("//ti:body", namespaces=nsmap):
                body.set("n", "urn:cts:frenchLit:pos{0}.pos{1}.positionThese-fr1".format(meta["promotion"], meta["id"]))

            # parts
            for body in template.xpath("//ti:body/ti:div[@n='2']", namespaces=nsmap):
                for part_id, part in enumerate(src_edition.xpath("//ti:body/ti:div", namespaces=nsmap)):
                    new_part = ET.fromstring("<div n='{0}' type='part'></div>".format(part_id+1))
                    for c in part.getchildren():
                        new_part.append(copy.deepcopy(c))
                    body.append(new_part)



            # write the edition file
            cts_edition = ET.tounicode(template, pretty_print=True)
            if not os.path.isfile(e_filepath):
                with open(e_filepath, 'w') as f:
                    f.write(cts_edition)

