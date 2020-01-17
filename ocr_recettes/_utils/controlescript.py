import click
import grammalecte
from lxml import etree
import json
from collections import Counter
import csv
from os import listdir
from os.path import isfile, join
from os import walk
import collections

#Renvoie la qualité de l'ocr du fichier xml
def ocrquality(xml_file):
    list_error_gram = []
    list_error_spell = []
    xslt = etree.parse("Extractionfichier.xsl")
    transform = etree.XSLT(xslt)
    text_file = transform(xml_file)
    text_file = str(text_file)
    oGrammarChecker = grammalecte.GrammarChecker("fr")
    #renvoie le fichier json des erreurs du fichier
    result_error = oGrammarChecker.generateParagraphAsJSON(0, text_file, bEmptyIfNoErrors=True)
    data_store = json.loads(result_error)
    for error in data_store.get("lGrammarErrors"):
        #Ajoute la valeur de l'erreur de grammaire dans une liste
        list_error_gram.append(error.get("sType"))
    for error in data_store.get("lSpellingErrors"):
        # Ajoute la valeur de l'erreur d'orthographe'dans une liste
        list_error_spell.append(error.get("sType"))
    #transforme la liste en dictionnaire pour connaitre le nombre des différents types d'erreur
    dict_error_spell = dict(Counter(list_error_spell))
    dict_error_gram = dict(Counter(list_error_gram))
    #renvoie une liste avec
    return [str(dict_error_spell), str(dict_error_gram)]

#check si la pagination a le bon ordre et si elle correspond au fichier de recollement
def pagination (xml_file, namespaces, d_recollement, name_file):
    '''

    :param xml_file: le fichier xml complet
    :param namespaces:
    :param d_recollement:
    :param name_file: nom du fichier xml
    :return: Renvoie une liste contenant en 1 si les pages sont dans le bon ordre 2 si la première et dernière page correspond au norme
    '''
    list_return = []
    listcontrol = []
    for page in xml_file.xpath("//tei:pb/@n", namespaces=namespaces):
        listcontrol.append(int(page))
    flag = 0
    i = 1
    while i < len(listcontrol):
        if (listcontrol[i] < listcontrol[i - 1]):
            flag = 1
        i += 1
    if (not flag):
        list_return.append(True)
    else:
        list_return.append(False)
    dict_file = d_recollement.get(name_file.split(".")[0])
    if dict_file.get("num:pp").split("-")[0] != listcontrol[0]:
        list_return.append("premier page non ok")
    elif dict_file.get("num:pp").split("-")[-1] != listcontrol[-1]:
        list_return.append("dernière page non ok")
    else :
        list_return.append("pagination ok")
    return list_return

#Controle si les metadata inscris correspondent
def structure_xml(xml_file):
    '''

    :param xml_file:
    :return:la liste contient: 1. l'appel au model, 2 le fichier est-il valide
    '''
    list_rep = []
    schema_present = str(etree.tostring(xml_file))
    if not '<?xml-model href="../theses_ocr.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>' in schema_present:
        list_rep.append(False)
    else :
        list_rep.append(True)
    schema = etree.RelaxNG(etree.parse("../theses_ocr.rng"))
    list_rep.append(schema.validate(xml_file))
    return list_rep

#controle le titre et le nom de l'auteur
def metadata_xml (xml_file, namespaces, d_recollement, name_file):
    '''

    :param xml_file:
    :param namespaces:
    :param d_recollement:
    :param name_file:
    :return: liste renvoie 1. nom d'auteur ok 2. nom de titre
    '''
    author = xml_file.find("//tei:author", namespaces=namespaces)
    title = xml_file.find("//tei:title", namespaces=namespaces)
    dict_file = d_recollement.get(name_file.split(".")[0])
    list_rep = []
    if author.text == "{} {}".format(dict_file.get("site :prenom"), dict_file.get("site :nom")):
        list_rep.append(True)
    else:
        list_rep.append(False)
    if title.text == dict_file.get("site :titre"):
        list_rep.append(True)
    else:
        list_rep.append(False)
    return list_rep

#Controle si toutes les images dans le fichier xml ont été analysées
def check_image(xml_file, namespaces, name_file):
    '''

    :param xml_file:
    :param namespaces:
    :param name_file:
    :return: Renvoie True si toutes les images envoyées ont été numérisées et oscérisées
    '''
    listcontrol = []
    for page in xml_file.xpath("//tei:pb/@facs", namespaces=namespaces):
        listcontrol.append(page.split("/")[-1])
    mypath = "/media/corentink/INTENSO/IIIF_Image/ENCPOS/{}/{}/TIFF/".format(name_file.split("_")[1],name_file.split(".")[0])
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    if onlyfiles == listcontrol:
        return True
    else:
        return False


def flat_gen(x):
    def iselement(e):
        return not(isinstance(e, collections.Iterable) and not isinstance(e, str))
    for el in x:
        if iselement(el):
            yield el
        else:
            yield from flat_gen(el)


def open_file(name_file):
    tree = etree.parse("../ENCPOS_{}/{}".format(name_file.split("_")[1], name_file))
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    d_recollement = {}
    with open("ENCPOS_recolement_BENC.csv",newline='') as csvfile:
        fichierrecollement = csv.reader(csvfile, delimiter='\t', quotechar='|')
        flag = True
        for lignerecollement in fichierrecollement:
            tempd = {}
            if flag is True :
                listindex = lignerecollement
                flag = False
            for x in range(len(listindex)):
                try :
                    tempd[listindex[x]] = lignerecollement[x]
                except :
                   continue
            try :
                d_recollement[lignerecollement[6]] = tempd
            except:
                break

    rep_pagination = pagination(tree, namespaces, d_recollement, name_file)
    rep_check_image = check_image(tree, namespaces, name_file)
    rep_ocr = ocrquality(tree)
    rep_structure = structure_xml(tree)
    rep_metadata = metadata_xml(tree, namespaces, d_recollement, name_file)
    return list(flat_gen([name_file, rep_pagination, rep_check_image,rep_ocr, rep_structure,rep_metadata]))


def check_files_folder (name, list_file):
    '''

    :param name:
    :param list_file:
    :return: Affiche si tous les fichiers ont été traités par le prestataire ou non
    '''
    list_nfile = []
    for nfile in list_file:
        list_nfile.append(nfile.split(".")[0])
    #Vérifie si tous les fichiers xml appellent toutes les dossiers existants
    if name[-1] == "*":
        for x in range(0, 10):
            list_dir_controle = []
            for root, dirs, files in walk("/media/corentink/INTENSO/IIIF_Image/ENCPOS/{}".format(name[:-1]+str(x))):
                for d in dirs:
                    if d != "TIFF" and d != "PDF":
                        list_dir_controle.append(d)
            list_diff = list(set(list_dir_controle) - set(list_nfile))
            print("199{}: position manquante :".format(x) + str(sorted(list_diff)))

    else:
        list_dir_controle = []
        for root, dirs, files in walk("/media/corentink/INTENSO/IIIF_Image/ENCPOS/{}".format(list_file[0].split("_")[1])):
            for d in dirs:
                if d != "TIFF" and d != "PDF":
                    list_dir_controle.append(d)
        print(list(set(list_dir_controle) - set(list_nfile)))


def recup_files_xml(name_folder):
    '''

    :param name_folder:
    :return: renvoie la liste des noms des fichiers à traiter
    '''
    #récupère la liste des fichiers xml présent dans le fichier demandé
    list_name = []
    #Si un seul fichier demandé
    if ".xml" in name_folder:
        list_name.append(name_folder)
        #si on demande de traiter une décénnie
    elif name_folder[-1] == "*":
        for x in range(0, 10):
            for root, dirs, files in walk("/home/corentink/Bureau/theses/ocr_recettes/ENCPOS_{}".format(name_folder[:-1]+str(x))):
                for name in files:
                    list_name.append(name)
    #Traite une année
    else:
        for root, dirs, files in walk("/home/corentink/Bureau/theses/ocr_recettes/ENCPOS_{}".format(name_folder)):
            for name in files:
                list_name.append(name)
    return list_name


@click.command()
@click.argument('name')
def main(name):
    list_file = recup_files_xml(name)
    check_files_folder(name, list_file)
    list_control = []
    list_control.append(["article","Suite logique des pages", "1er - dernier page correspond avec le fichier de recollement","Toutes les images envoyés numérisés", "Faute d'orthographe","Faute de typographie","Schéma présent","Fichier valide","Nom de l'auteur", "Titre de la thèse" ])
    for name_file in list_file:
        list_control.append(open_file(name_file))
    f = open('numbers2.csv', 'w')
    with f:
        writer = csv.writer(f)
        for row in list_control:
            print(row)
            writer.writerow(row)

if __name__ == "__main__":
    main()
