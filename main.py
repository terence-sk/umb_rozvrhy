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
import os
import requests
from bs4 import BeautifulSoup
from lxml import etree


def add_days_of_week_xml(root):
    pondelok = etree.Element('pondelok')
    utorok = etree.Element('utorok')
    streda = etree.Element('streda')
    stvrtok = etree.Element('stvrtok')
    piatok = etree.Element('piatok')
    root.append(pondelok)
    root.append(utorok)
    root.append(streda)
    root.append(stvrtok)
    root.append(piatok)


def add_class_to_xml(root, clazz):

    if clazz[6] is not None:
        print "Spracuvam " + clazz[6]

    den = None
    # Keby chceme zmenit clazz[3] nepojde to lebo tuple sa neda zmenit
    den_string = clazz[3]
    if not clazz[3] is None:
        if den_string == u'štvrtok':
            den_string = 'stvrtok'
        den = root.find(den_string)
    else:
        if clazz[0] is not None:
            print "***** Nepodarilo sa ziskat den pre hodinu: " + clazz[0] + " Rozvrh moze byt nekompletny alebo hodiny posunute *****"
        elif clazz[0] is None and clazz[6] is not None:
            print "***** PRAZDNY ROZVRH *****" + clazz[6]
        else:
            print "***** Rozvrh ktory nema ani nadpis *****"

    if den is not None:

        if not clazz[0] is None:
            hodina = etree.Element('hodina')
            hodina.text = clazz[0]
            den.append(hodina)

        if not clazz[1] is None:
            vyucujuci = etree.Element('vyucujuci')
            vyucujuci.text = clazz[1]
            den.append(vyucujuci)

        if not clazz[2] is None:
            ucebna = etree.Element('ucebna')
            ucebna.text = clazz[2]
            den.append(ucebna)

        if not clazz[4] is None:
            zaciatok = etree.Element('zaciatok')
            zaciatok.text = clazz[4]
            den.append(zaciatok)

        if not clazz[5] is None:
            trvanie = etree.Element('trvanie')
            trvanie.text = clazz[5]
            den.append(trvanie)

    # root.append(den)


def get_class_length(title):
    return title['colspan']


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

    print "Ziskavam rozvrh z URL " + url

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
        if predmet.text == '':
            predmety.append('chyba nazov predmetu')
        else:
            predmety.append(predmet.text)
    for ucitel in soup.find_all("font", {'class': 'Vyucujuci'}):
        if ucitel.text == '':
            ucitelia.append('chyba ucitel')
        else:
            ucitelia.append(ucitel.text)
    for ucebna in soup.find_all("font", {'class': 'Ucebna'}):
        if ucebna.text == '':
            ucebne.append('chyba ucebna')
        else:
            ucebne.append(ucebna.text)

    ciste_trka = soup.find_all("tr", {'class': False})
    ciste_trka = ciste_trka[1:-1]  # Vyhodime to trko ktore to obsahuje vsetko, to nepotrebujem

    for trko in ciste_trka:
        if trko != '\n' and trko.find("td", {'class': 'HlavickaDni'}) is not None:
                hlavicka_dni = trko.find("td", {'class': 'HlavickaDni'})['title']

                hodiny = trko.find("td", {'class': 'HlavickaDni'}).parent.find_all("td") #vsetky hodiny v ramci toho dna
                # podla bgcolor viem ci je hodina alebo volnahodina
                for hodinaInfo in hodiny:
                    if hodinaInfo.has_attr('bgcolor') or hodinaInfo.attrs['class'][0] == 'Hod':
                        pocHod.append(get_class_length(hodinaInfo))
                        dni.append(hlavicka_dni)
                        zacinaHod.append(get_class_start(hodinaInfo))

        # Ked je dve a viac predmetov v tom istom case a tom istom dni, tak ta druha alebo tretia
        # je mimo hlavneho <tr> tagu v ktorom sa nachadza aj nazov dna, a preto treba hladat
        # dalsie hodiny mimo tr tagu.
        elif trko != '\n' and trko.find_all("td") is not None:
            for hodinaMimoTr in trko.find_all("td"):
                if hodinaMimoTr.has_attr('bgcolor') or hodinaInfo.attrs['class'][0] == 'Hod':
                    pocHod.append(get_class_length(hodinaMimoTr))
                    dni.append(hlavicka_dni)
                    zacinaHod.append(get_class_start(hodinaMimoTr))
    # Ak aj ucebna alebo meno vyucujuceho chyba, dlzka vsetkych zoznamov bude tak ci tak rovnaka
    # avsak v pripade "Nadpis", ten bude vzdy len jeden, preto musime pouzit "izip_longest"
    # ktory zo zoznamu kratsej dlzky, spravi dlhsi a doplni tam "None". keby to nespravim, kazdy
    # zoznam skrati na jednu polozku a to by nam chybali hodiny...

    # No a navyse je potrebne odstranit predmet ktory ma v nazve tri hviezdy pretoze ten ma v sebe
    # data o dalsich hodinach a tie sa nedaju normalne sparsovat, teda ich odstranim. Keby to neodstranim
    # hodiny sa mozu posunut a byt v nespravnych dnoch a mat zle ucebne
    if u'***' in predmety:
        predmety.remove(u'***')
    mojList = list(itertools.izip_longest(predmety, ucitelia, ucebne, dni, zacinaHod, pocHod, nadpis))

    return mojList


url = "http://www.pdf.umb.sk/~jsedliak/Public/"
# tento string je v kazdom linku pre konkretnu triedu, nespracuvame teda ucitelske rozvhy
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
urls = urls[1:-1]

cele_rozvrhy_tried = []
#for mojaUrl in urls:
cele_rozvrhy_tried.append(get_lessons_of_class("http://www.pdf.umb.sk/~jsedliak/Public/rozvrh_tr2985.htm")) #TODO naspat zmeny ked uz nebudem chciet generovat len jeden rozvrh

# spravime si zlozku na rozvrhy
try:
    os.makedirs('rozvrhy')
except OSError:
    pass  # ak uz zlozka existuje da error, ten ignorujeme, chceme zapisat do zlozky

for rozvrh_jednej_triedy in cele_rozvrhy_tried:
    trieda_nazov = rozvrh_jednej_triedy[0][6]  # 6ty index obsahuje meno triedy ktorej patri rozvrh
    root = etree.Element("rozvrh")
    root.attrib['Trieda'] = trieda_nazov
    add_days_of_week_xml(root)

    vyuc_hodiny = []

    for jedna_hodina_rozvrhu in rozvrh_jednej_triedy:
        add_class_to_xml(root, jedna_hodina_rozvrhu)
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

    zoznam_dni = [pondelok, utorok, streda, stvrtok, piatok]

    for den in zoznam_dni:
        for objekt_hodina in den:
            ODTCreator.add_values(objekt_hodina.hodina,
                                  objekt_hodina.vyuc,
                                  objekt_hodina.ucebna,
                                  objekt_hodina.den,
                                  objekt_hodina.zaciatok,
                                  objekt_hodina.trvanie)

    # ODTCreator.align_cells('pondelok')
    # ODTCreator.align_cells('utorok')
    # ODTCreator.align_cells('streda')
    # ODTCreator.align_cells('stvrtok')
    # ODTCreator.align_cells('piatok')

    f = open('rozvrhy/' + trieda_nazov + '.xml', 'w')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()

