import os
import lxml.etree as ET


class PositionThese:

    def __init__(self, metadata, textgroup_template, workgroup_template):
        self.__tg_template_filename = textgroup_template
        self.__wg_template_filename = workgroup_template
        self.__metadata = {}

        clean = lambda s: s[1:-1].strip()

        with open(metadata, 'r') as meta:
            for line in meta.readlines()[1::]:
                line = line.split(",")
                print(line)
                line.extend([""]*(13-(len(line)-1)))

                titres = clean(line[6]).split(".")

                self.__metadata[line[0]] = {
                    "id" : line[0],
                    "promotion" : line[1],
                    "tri": line[2],
                    "nom": line[3],
                    "prenom": line[4],
                    "sexe": line[5],
                    "titre": "",
                    "notBefore": line[7],
                    "notAfter": line[8],
                    "authorKey": line[9],
                    "authorRef": line[10],
                    "ppn_position": line[11],
                    "ppn_these": line[12],
                    "an_these": line[13],
                    "sous_titre": ""
                }

                self.__metadata[line[0]]["titre"] = titres[0].strip()
                if len(titres) > 1:
                    self.__metadata[line[0]]["sous_titre"] = titres[1].strip()

    @property
    def __tg_template(self): return ET.parse(self.__tg_template_filename)

    @property
    def __wg_template(self): return ET.parse(self.__wg_template_filename)

    def write_textgroup(self, pos_year, dest_path):
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
            if not os.path.isdir(w_dirname):
                os.makedirs(w_dirname)

            w_filepath = os.path.join(w_dirname, "__cts__.xml")
            if not os.path.isfile(w_filepath):
                with open(w_filepath, 'w') as f:
                    cts_wg = ET.tounicode(template, pretty_print=True)
                    f.write(cts_wg)
                    #print(cts_wg)


    def write_edition(self, pos_year, dest_path):
        pass
        #template = self.__edition_template
        for meta in [m for m in self.__metadata.values() if m["promotion"] == pos_year]:
            e_dirname = os.path.join(dest_path, "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]))

            e_filepath = os.path.join(e_dirname, "{0}.{1}.{2}".format(
                "pos{0}".format(meta["promotion"]), "pos{0}".format(meta["id"]),"positionThese-fr1.xml"
            ))

            if not os.path.isfile(e_filepath):
                with open(e_filepath, 'w') as f:
                    pass
                    #cts_wg = ET.tounicode(template, pretty_print=True)
                    #f.write(cts_wg)
                    # print(cts_wg)