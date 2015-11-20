# coding=utf-8
# Martin Svonava
# program sluzi na parsovanie HTML rozvrhov na UMBcke
# a tvorbu XMLka ktore sa da dalej spracovavat
import itertools
import os
import requests
from bs4 import BeautifulSoup
from lxml import etree


def add_days_of_week_xml(root):
    pondelok = etree.Element('pondelok')
    utorok = etree.Element('utorok')
    streda = etree.Element('streda')
    stvrtok = etree.Element("stvrtok")
    piatok = etree.Element('piatok')
    root.append(pondelok)
    root.append(utorok)
    root.append(streda)
    root.append(stvrtok)
    root.append(piatok)


#class je rezervovane pythonom, musi to byt clazz :)
def add_class_to_xml(root, clazz):

    hodina = etree.Element('hodina')
    hodina.text = clazz[0]

    vyucujuci = etree.Element('vyucujuci')
    vyucujuci.text = clazz[1]

    ucebna = etree.Element('ucebna')
    ucebna.text = clazz[2]

    den = root.find(clazz[3]) #TODO co v pripadoch ked chyba den.. omg, treba prerobit tak aby den bralo z <tr>

    zaciatok = etree.Element('zaciatok')
    zaciatok.text = clazz[4]

    trvanie = etree.Element('trvanie')
    trvanie.text = clazz[5]

    den.append(hodina)
    den.append(vyucujuci)
    den.append(ucebna)
    den.append(zaciatok)
    den.append(trvanie)


def get_class_length(title):
    return title['colspan']


#blizsi popis vo funkcii get_class_start
def get_class_day(title):
    den = title['title'].partition('*')[-1].rpartition('*')[0].replace(" ", "").split(':')[0]
    # ach slovencina... keby to nechame tak, vo vystupnom xml by nebol tag štvrtok
    # ale #357tvrtok alebo tak nejak
    if den == u'štvrtok':
        return "stvrtok"
    return den


def get_class_start(title):
    # title obsahuje nieco ako "* streda : 14-15 *" - potrebujem dostat len prve cislo
    # pretoze aka dlha hodina bude viem z ineho atributu (pozri funkciu get_lessons_of_class, colspan)
    # toto mi vrati pole obsahujuce ['streda', '14-15'], vezmem prvy index cize cisla 14-15
    zacHod = title['title'].partition('*')[-1].rpartition('*')[0].replace(" ", "").split(':')[1]

    # 1 alebo 15 to je v poriadku
    # 1-2 a 9-10 -> v oboch pripadoch chcem len prve cislo (dlzka 3 a 4)
    # 12-13 -> tu chcem prve dve cisla (dlzka 5)

    if len(zacHod) == 3 or len(zacHod) == 4:
        return zacHod[0:1]
    if len(zacHod) == 5:
        return zacHod[0:2]
    return zacHod


def get_lessons_of_class(url):

    print "Getting lessons of " + url

    source = requests.get(url)
    text = source.text
    soup = BeautifulSoup(text, "html.parser")

    predmety = []
    ucitelia = []
    ucebne = []

    dni = []
    zacinaHod = []
    pocHod = []

    nadpis = []
    # neni to bohvieako pekne ale budiz, v nultom indexe je nazov skoly, v prvom Triedy
    nadpis.append(soup.find_all(("div", {'class': 'Nadpis'}))[1].text)

    for predmet in soup.find_all("font", {'class': 'Predmet'}):
        predmety.append(predmet.text)
    for ucitel in soup.find_all("font", {'class': 'Vyucujuci'}):
        ucitelia.append(ucitel.text)
    for ucebna in soup.find_all("font", {'class': 'Ucebna'}):
        ucebne.append(ucebna.text)

    hodiny = soup.find_all("td")

    #TODO Zober vsetky <tr>
    #TODO Zober td class hlavicka dni text
    #TODO Zober vsetky td... to uz mam vlastne hotove


    # podla bgcolor viem ci je hodina ale volnahodina
    for hodinaInfo in hodiny:
        if hodinaInfo.has_attr('bgcolor'): # ak ma bgcolor nie je to Volna hodina ani nic ine
            pocHod.append(get_class_length(hodinaInfo))
            dni.append(get_class_day(hodinaInfo))
            zacinaHod.append(get_class_start(hodinaInfo))

    # Ak aj ucebna alebo meno vyucujuceho chyba, dlzka vsetkych zoznamov bude tak ci tak rovnaka
    # avsak v pripade "Nadpis", ten bude vzdy len jeden, preto musime pouzit "izip_longest"
    # ktory zo zoznamu kratsej dlzky, spravi dlhsi a doplni tam "None". keby to nespravim, kazdy
    # zoznam skrati na jednu polozku a to by nam chybali hodiny...
    return list(itertools.izip_longest(predmety, ucitelia, ucebne, dni, zacinaHod, pocHod, nadpis))


url = "http://www.pdf.umb.sk/~jsedliak/Public/"
#tento string je v kazdom linku pre konkretnu triedu, nespracuvame teda ucitelske rozvhy
rozvrh_tried = "rozvrh_tr"
urls = []

source = requests.get(url)
text = source.text
soup = BeautifulSoup(text, "html.parser")

# Zobere vsetky linky a pozrie sa ci link obsahuje "rozvrh_tr", aby sa spracovali len rozvrhy tried
for link in soup.find_all("a"):
    toAppend = link.text
    if rozvrh_tried in toAppend:
        final_url = url + toAppend
        urls.append(final_url)

# vyhodi sa prvy link ktory neobsahuje konkretnu triedu, ale sablonu pre vsetky triedy
urls = urls[1:10] #TODO [1:-1]

lessons = []
for mojaUrl in urls:
    lessons.append(get_lessons_of_class(mojaUrl))

#spravime si zlozku na rozvrhy
try:
    os.makedirs('rozvrhy')
except OSError:
    pass #ak uz zlozka existuje da error, ten ignorujeme, chceme zapisat do zlozky

# prvy index je cela hodina aj vyuc aj ucebna
# druhy index je hodina osobite, vyuc osobite..
for clazz in lessons:
    root = etree.Element("rozvrh")
    print lessons[0][0][6]
    root.attrib['Trieda'] = lessons[0][0][6] # 6ty index obsahuje meno triedy ktorej patri rozvrh
    add_days_of_week_xml(root)

    for x in clazz:
        add_class_to_xml(root, x)


    f = open('rozvrhy/' + lessons[0][0][6] + '.xml', 'w')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()
# clazz[0]  Nazov hodiny
# clazz[1]  Vyucujuci
# clazz[2]  Ucebna
# clazz[3]  Den
# clazz[4]  Zaciatok
# clazz[5]  Trvanie
# clazz[6]  Nazov Triedy pre ktoru rozvrh plati


