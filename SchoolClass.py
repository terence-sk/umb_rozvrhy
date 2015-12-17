class SchoolClass(object):
    nazovHodiny = ""
    vyuc = ""
    ucebna = ""
    den = ""
    zaciatok = ""
    trvanie = ""
    nazovTriedy = ""

    def __init__(self, nazovHodiny, vyuc, ucebna, den, zaciatok, trvanie, nazovTriedy):
        self.nazovHodiny = nazovHodiny
        self.vyuc = vyuc
        self.ucebna = ucebna
        self.den = den
        self.zaciatok = zaciatok
        self.trvanie = trvanie
        self.nazovTriedy = nazovTriedy


def make_class(nazovHodiny, vyuc, ucebna, den, zaciatok, trvanie, nazovTriedy):
    sc = SchoolClass(nazovHodiny, vyuc, ucebna, den, zaciatok, trvanie, nazovTriedy)
    return sc
