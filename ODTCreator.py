# coding=utf-8
from lxml import etree
import unicodedata


def open_base_file():
    file_odt = open('base_xml.xml', 'r')
    xml_data = file_odt.read()
    file_odt.close()
    return etree.fromstring(xml_data)


def save_changes(root):
    file_output = open('content.xml', 'w')
    file_output.write(etree.tostring(root, pretty_print=True))
    file_output.close()


# prida title tabulke (nazov triedy)
def add_class_title(title):
    pass #TODO

root = open_base_file()


#Prida 3 stringy hodina/vyuc/trieda do tabulky, den urci riadok, zaciatok stlpec, trvanie colspan
def add_values(hodina, vyucujuci, trieda, den, zaciatok, trvanie):
    # Toto je okej vzdy
    row = root.findall("office:body/office:text/table:table/table:table-row", root.nsmap)[get_day_number(den)]

    # ak mame hodinu ktora je natiahnuta cez dve alebo viac hodin, v riadku je menej cells po kazdej takejto pridanej hodine
    # sa musi znova vypocitat o kolko sa ma hodina posunut
    num_of_cells_default = 19
    num_of_cells_real = len(row.findall("table:table-cell", root.nsmap))
    num_of_cells_in_row_missing = num_of_cells_default - num_of_cells_real

    zaciatok = str(int(zaciatok)-num_of_cells_in_row_missing)

    cell = row.findall("table:table-cell", root.nsmap)[int(zaciatok)]
    cell_text = cell.findall("text:p", root.nsmap)[0]  #text bude v table cell vzdy iba jeden

    # ak su dve hodiny v tom istom case ktore su dlhsie ako jednu hodinu, odstrani sa cell ako vzdy
    # ta druha by sa ale posunula o jednu spat, pretoze sa vyrata posun pred pridavanim, a preto treba pricitat jednotku
    plus_one = 0 if len(cell.findall("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}covered-table-cell")) == 0 else 1

    # teraz treba nanovo najst cell do ktoreho pridame tu posunutu hodinu
    if plus_one == 1:
        zaciatok = str(int(zaciatok)+plus_one)
        cell = row.findall("table:table-cell", root.nsmap)[int(zaciatok)]
        cell_text = cell.findall("text:p", root.nsmap)[0]

    if int(trvanie) > 1:
        i = 1
        # odstranujeme cells podla toho cez kolko hodin sa vyucovanie natiahne
        while i < int(trvanie) and len(cell.findall("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}covered-table-cell")) == 0:
            next_cell = row.findall("table:table-cell", root.nsmap)[int(zaciatok)+i]
            row.remove(next_cell)
            i += 1
        # ak sa v tom cell nenachadza table:covered-table-cell, ktora odstranuje ciary medzi spojenymi cellmi
        # tak ju mozme pridat. staci vsak len jedna, preto kontrolujeme ci tam ziadna nie je
        if len(cell.findall("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}covered-table-cell")) == 0:
            cell.attrib['{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-spanned'] = trvanie
            cell.append(etree.Element("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}covered-table-cell"))

    # v cell v ktorych nebola ziadna hodina nemaju atribut text vyplneny
    if cell_text.text is None:
                cell_text.text = ''

    # diakritika robi problemy, dame ju prec (stenu dame prec, katarina brychtova posta pre teba :D)
    hodina = unicodedata.normalize('NFKD', hodina).encode('ascii','ignore')
    vyucujuci = unicodedata.normalize('NFKD', vyucujuci).encode('ascii','ignore')
    trieda = unicodedata.normalize('NFKD', trieda).encode('ascii','ignore')

    text_final = hodina + vyucujuci + trieda
    cell_text.text += text_final + "___ " # podtrzniky pre vizualne oddelenie viacerych hodin v tom istom case

    save_changes(root)


# vrati int ako hodnotu riadku. Riadok 0 poradie hodin
def get_day_number(den):
    if den == 'pondelok':
        return 1
    if den == 'utorok':
        return 2
    if den == 'streda':
        return 3
    if den == 'stvrtok' or den == u'štvrtok':
        return 4
    if den == 'piatok':
        return 5
