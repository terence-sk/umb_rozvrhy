# coding=utf-8
from lxml import etree
import unicodedata


def open_base_file():
    file_odt = open('base_xml.xml', 'r')
    xml_data = file_odt.read()
    file_odt.close()
    return etree.fromstring(xml_data)


def save_changes(root):
    file_output = open('output_odt.xml', 'r+')
    file_output.write(etree.tostring(root, pretty_print=True))
    file_output.close()


# prida title tabulke (nazov triedy)
def add_class_title(title):
    pass #TODO

root = open_base_file()


#Prida 3 stringy hodina/vyuc/trieda do tabulky, den urci riadok, zaciatok stlpec, trvanie colspan
def add_values(hodina, vyucujuci, trieda, den, zaciatok, trvanie):

    row = root.findall("office:body/office:text/table:table/table:table-row", root.nsmap)[get_day_number(den)]
    cell = row.findall("table:table-cell", root.nsmap)[int(zaciatok)]
    cell_text = cell.findall("text:p", root.nsmap)[0] #text bude v table cell vzdy iba jeden

    hodina = unicodedata.normalize('NFKD', hodina).encode('ascii','ignore')
    vyucujuci = unicodedata.normalize('NFKD', vyucujuci).encode('ascii','ignore')
    trieda = unicodedata.normalize('NFKD', trieda).encode('ascii','ignore')

    if cell_text.text is None:
        cell_text.text = ''

    text_final = hodina + vyucujuci + trieda
    cell_text.text += text_final + "___ " # podtrzniky pre oddelenie viacerych hodin v tom istom case

    if int(trvanie) > 1:
        i = 1
        while i < int(trvanie):
            next_cell = row.findall("table:table-cell", root.nsmap)[int(zaciatok)+i]
            next_cell_text = next_cell.findall("text:p", root.nsmap)[0]
            if next_cell_text.text is None:
                next_cell_text.text = ''
            next_cell_text.text += text_final + "___ "
            i += 1

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
