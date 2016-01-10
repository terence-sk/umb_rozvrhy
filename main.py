# coding=utf-8
# Martin Svonava
# program sluzi na parsovanie HTML rozvrhov na UMBcke
# a tvorbu XMLka ktore sa da dalej spracovavat
# >>>> Struktura dat <<<<
# [0]  Nazov hodiny
# [1]  Vyucujuci
# [2]  Ucebna
# [3]  Den
# [4]  Zaciatok
# [5]  Trvanie
# [6]  Nazov Triedy pre ktoru rozvrh plati
from operator import attrgetter
import ODTCreator
import SchoolClass
import itertools
import subprocess
import os
import requests
from bs4 import BeautifulSoup
from lxml import etree

# URL Kde sa nachadzaju rozvrhy
url = "http://www.pdf.umb.sk/~jsedliak/Public/"

# "konstanty" ktore rozhoduju o tom ake XMLka sa generuju
XML_ONLY = 0
ODT_ONLY = 1
BOTH_XML_ODT = 2


def add_days_of_week_xml(root):
    pon = etree.Element('pondelok')
    uto = etree.Element('utorok')
    ste = etree.Element('streda')
    stv = etree.Element('stvrtok')
    pia = etree.Element('piatok')
    root.append(pon)
    root.append(uto)
    root.append(ste)
    root.append(stv)
    root.append(pia)


def add_class_to_xml(root, clazz):

    if clazz[6] is not None:
        print "Spracuvam " + clazz[6]

    day = None
    # Keby chceme zmenit clazz[3] nepojde to lebo tuple sa neda zmenit
    den_string = clazz[3]
    if not clazz[3] is None:
        if den_string == u'štvrtok':
            den_string = 'stvrtok'
        day = root.find(den_string)
    else:
        if clazz[0] is not None:
            print "Nepodarilo sa ziskat den pre " + clazz[0] + ". Rozvrh moze byt nekompletny alebo hodiny posunute"
        elif clazz[0] is None and clazz[6] is not None:
            print "***** Prazdny rozvrh *****" + clazz[6]
        else:
            print "***** Rozvrhu chyba nadpis *****"

    if day is not None:

        if not clazz[0] is None:
            hodina = etree.Element('hodina')
            hodina.text = clazz[0]
            day.append(hodina)

        if not clazz[1] is None:
            vyucujuci = etree.Element('vyucujuci')
            vyucujuci.text = clazz[1]
            day.append(vyucujuci)

        if not clazz[2] is None:
            ucebna = etree.Element('ucebna')
            ucebna.text = clazz[2]
            day.append(ucebna)

        if not clazz[4] is None:
            zaciatok = etree.Element('zaciatok')
            zaciatok.text = clazz[4]
            day.append(zaciatok)

        if not clazz[5] is None:
            trvanie = etree.Element('trvanie')
            trvanie.text = clazz[5]
            day.append(trvanie)


def get_class_length(title):
    return title['colspan']


def get_class_start(title):
    # title obsahuje nieco ako "* streda : 14-15 *" - potrebujem dostat len prve cislo
    # pretoze aka dlha hodina bude viem z ineho atributu (pozri funkciu get_lessons_of_class, colspan)
    # toto mi vrati pole obsahujuce ['streda', '14-15'], vezmem prvy index cize cisla 14-15
    zac_hod = title['title'].partition('*')[-1].rpartition('*')[0].replace(" ", "").split(':')[1]

    # 1 alebo 15 to je v poriadku
    # 1-2 a 9-10 -> v oboch pripadoch chcem len prve cislo (dlzka 3 a 4)
    # 12-13 -> tu chcem prve dve cisla (dlzka 5)

    if len(zac_hod) == 3 or len(zac_hod) == 4:
        return zac_hod[0:1]
    if len(zac_hod) == 5:
        return zac_hod[0:2]
    return zac_hod


def get_lessons_of_class(url_class):

    print "Ziskavam rozvrh z URL " + url_class

    src = requests.get(url_class)
    txt = src.text
    bsoup = BeautifulSoup(txt, "html.parser")

    predmety = []
    ucitelia = []
    ucebne = []

    dni = []
    zacina_hod = []
    poc_hod = []

    # neni to bohvieako pekne ale budiz, v nultom indexe je nazov skoly, v prvom Triedy
    nadpis = [bsoup.find_all(("div", {'class': 'Nadpis'}))[1].text]

    for predmet in bsoup.find_all("font", {'class': 'Predmet'}):
        if predmet.text == '':
            predmety.append('chyba nazov predmetu')
        else:
            predmety.append(predmet.text)
    for ucitel in bsoup.find_all("font", {'class': 'Vyucujuci'}):
        if ucitel.text == '':
            ucitelia.append('chyba ucitel')
        else:
            ucitelia.append(ucitel.text)
    for ucebna in bsoup.find_all("font", {'class': 'Ucebna'}):
        if ucebna.text == '':
            ucebne.append('chyba ucebna')
        else:
            ucebne.append(ucebna.text)

    ciste_trka = bsoup.find_all("tr", {'class': False})
    ciste_trka = ciste_trka[1:-1]  # Vyhodime to trko ktore to obsahuje vsetko, to nepotrebujem

    for trko in ciste_trka:
        if trko != '\n' and trko.find("td", {'class': 'HlavickaDni'}) is not None:
                hlavicka_dni = trko.find("td", {'class': 'HlavickaDni'})['title']

                # vsetky hodiny v ramci toho dna
                hodiny = trko.find("td", {'class': 'HlavickaDni'}).parent.find_all("td")
                # podla bgcolor viem ci je hodina alebo volnahodina
                for hodinaInfo in hodiny:
                    if hodinaInfo.has_attr('bgcolor') or hodinaInfo.attrs['class'][0] == 'Hod':
                        poc_hod.append(get_class_length(hodinaInfo))
                        dni.append(hlavicka_dni)
                        zacina_hod.append(get_class_start(hodinaInfo))

        # Ked je dve a viac predmetov v tom istom case a tom istom dni, tak ta druha alebo tretia
        # je mimo hlavneho <tr> tagu v ktorom sa nachadza aj nazov dna, a preto treba hladat
        # dalsie hodiny mimo tr tagu.
        elif trko != '\n' and trko.find_all("td") is not None:
            for hodinaMimoTr in trko.find_all("td"):
                if hodinaMimoTr.has_attr('bgcolor') or hodinaInfo.attrs['class'][0] == 'Hod':
                    poc_hod.append(get_class_length(hodinaMimoTr))
                    dni.append(hlavicka_dni)
                    zacina_hod.append(get_class_start(hodinaMimoTr))
    # Ak aj ucebna alebo meno vyucujuceho chyba, dlzka vsetkych zoznamov bude tak ci tak rovnaka
    # avsak v pripade "Nadpis", ten bude vzdy len jeden, preto musime pouzit "izip_longest"
    # ktory zo zoznamu kratsej dlzky, spravi dlhsi a doplni tam "None". keby to nespravim, kazdy
    # zoznam skrati na jednu polozku a to by nam chybali hodiny...

    # No a navyse je potrebne odstranit predmet ktory ma v nazve tri hviezdy pretoze ten ma v sebe
    # data o dalsich hodinach a tie sa nedaju normalne sparsovat, teda ich odstranim. Keby to neodstranim
    # hodiny sa mozu posunut a byt v nespravnych dnoch a mat zle ucebne
    if u'***' in predmety:
        predmety.remove(u'***')
    moj_list = list(itertools.izip_longest(predmety, ucitelia, ucebne, dni, zacina_hod, poc_hod, nadpis))

    return moj_list


# Zobere vsetky linky a pozrie sa ci link obsahuje "rozvrh_tr", aby sa spracovali len rozvrhy tried
def remove_non_class_timetables(soup_links):
    modified_urls = []

    for link in soup_links.find_all("a"):
        to_append = link.text
        if "rozvrh_tr" in to_append:
            final_url = url + to_append
            modified_urls.append(final_url)

    return modified_urls


def get_urls_to_process():
    source = requests.get(url)
    text = source.text
    soup = BeautifulSoup(text, "html.parser")

    urls = remove_non_class_timetables(soup)

    # vyhodi sa prvy link ktory neobsahuje konkretnu triedu, ale sablonu pre vsetky triedy
    urls = urls[1:-1]
    return urls


def make_folder():
    # spravime si zlozku na rozvrhy
    try:
        os.makedirs('rozvrhy')
    except OSError:
        pass  # ak uz zlozka existuje da error, ten ignorujeme, chceme zapisat do zlozky


def generate_xmls(generate_xml):

    if generate_xml == XML_ONLY or generate_xml == BOTH_XML_ODT:
        cele_rozvrhy_tried = [get_lessons_of_class("http://www.pdf.umb.sk/~jsedliak/Public/rozvrh_tr2985.htm")]
        #cele_rozvrhy_tried = []
        #for url_to_process in get_urls_to_process():
        #    cele_rozvrhy_tried.append(get_lessons_of_class(url_to_process))

        for rozvrh_jednej_triedy in cele_rozvrhy_tried:
            trieda_nazov = rozvrh_jednej_triedy[0][6]  # 6ty index obsahuje meno triedy ktorej patri rozvrh
            rozvrh = etree.Element("rozvrh")
            rozvrh.attrib['Trieda'] = trieda_nazov
            add_days_of_week_xml(rozvrh)

            vyuc_hodiny = []

            for jedna_hodina_rozvrhu in rozvrh_jednej_triedy:
                add_class_to_xml(rozvrh, jedna_hodina_rozvrhu)
                vyuc_hodiny.append(SchoolClass.make_class(jedna_hodina_rozvrhu[0],
                                                          jedna_hodina_rozvrhu[1],
                                                          jedna_hodina_rozvrhu[2],
                                                          jedna_hodina_rozvrhu[3],
                                                          jedna_hodina_rozvrhu[4],
                                                          jedna_hodina_rozvrhu[5]))

            pondelok = []
            utorok = []
            streda = []
            stvrtok = []
            piatok = []

            for objekt_hodina in vyuc_hodiny:
                if objekt_hodina.den == 'pondelok':
                    pondelok.append(objekt_hodina)
                if objekt_hodina.den == 'utorok':
                    utorok.append(objekt_hodina)
                if objekt_hodina.den == 'streda':
                    streda.append(objekt_hodina)
                if objekt_hodina.den == u'štvrtok':
                    stvrtok.append(objekt_hodina)
                if objekt_hodina.den == 'piatok':
                    piatok.append(objekt_hodina)

            pondelok.sort(key=attrgetter('zaciatok'))
            utorok.sort(key=attrgetter('zaciatok'))
            streda.sort(key=attrgetter('zaciatok'))
            stvrtok.sort(key=attrgetter('zaciatok'))
            piatok.sort(key=attrgetter('zaciatok'))

        if generate_xml == ODT_ONLY or generate_xml == BOTH_XML_ODT:

            zoznam_dni = [pondelok, utorok, streda, stvrtok, piatok]

            for den in zoznam_dni:
                for objekt_hodina in den:
                    ODTCreator.add_values(objekt_hodina.hodina,
                                          objekt_hodina.vyuc,
                                          objekt_hodina.ucebna,
                                          objekt_hodina.den,
                                          objekt_hodina.zaciatok,
                                          objekt_hodina.trvanie)

            ODTCreator.align_cells('pondelok')
            ODTCreator.align_cells('utorok')
            ODTCreator.align_cells('streda')
            ODTCreator.align_cells('stvrtok')
            ODTCreator.align_cells('piatok')

        f = open('rozvrhy/' + trieda_nazov + '.xml', 'w')
        f.write(etree.tostring(rozvrh, pretty_print=True))
        f.close()

    # Won't work in Windows
    subprocess.call(['./packNrun.sh'])

generate_xmls(BOTH_XML_ODT)