from unittest import TestCase

from elex3.lib.parser import clean_office, clean_party


class TestDataCleaners(TestCase):


    def test_clean_office_rep(self):
        self.assertEquals(clean_office('U.S. Rep - 1'), ('U.S. House of Representatives', 1))

    def test_clean_office_other(self):
        self.assertEquals(clean_office('U.S. Senate'), ('U.S. Senate', ''))

    def test_clean_party_gop(self):
        self.assertEquals(clean_party('GOP'), 'REP')

    def test_clean_party_dem(self):
        self.assertEquals(clean_party('Democratic'), 'DEM')

    def test_clean_party_others(self):
        self.assertEquals(clean_party('Green'), 'GREEN')

