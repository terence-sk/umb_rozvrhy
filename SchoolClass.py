class SchoolClass(object):
    hodina = ""
    vyuc = ""
    ucebna = ""
    den = ""
    zaciatok = ""
    trvanie = ""

    def __init__(self, hodina, vyuc, ucebna, den, zaciatok, trvanie):
        self.hodina = hodina
        self.vyuc = vyuc
        self.ucebna = ucebna
        self.den = den
        self.zaciatok = zaciatok
        self.trvanie = trvanie


def make_class(hodina, vyuc, ucebna, den, zaciatok, trvanie):
    if zaciatok is not None:
        sc = SchoolClass(hodina, vyuc, ucebna, den, int(zaciatok), trvanie)
    else:
        sc = SchoolClass(hodina, vyuc, ucebna, den, zaciatok, trvanie)
    return sc
