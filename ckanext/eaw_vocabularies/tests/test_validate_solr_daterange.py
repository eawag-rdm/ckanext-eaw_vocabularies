from ckanext.eaw_vocabularies.validate_solr_daterange import SolrDaterange
import ckan.plugins.toolkit as tk
import pytest

class TestSolrDaterange(object):

    fail = {'year': ['986z', '87t65', '876', '-456', '06754', '-06411', '87.9'],
            'month': ['u4', '011', '6', '-1', '123'],
            'day': ['9', '076', '8i', ' 2'],
            'hour': ['3', '8z', '022', '24', '-2'], 
            'minute': ['1', '012', '3i', '.'],
            'second': ['7Z', '60Z', '023Z', '00.Z', '12', '12.23']
    }
    pas = {'year': ['2016', '0638', '-0124', '45919', '-72354393'],
           'month': ['02', '10', '12', '00'],
           'day': ['00', '35'],
           'hour': ['00', '15', '23'],
           'minute': ['00', '23', '59'],
           'second': ['00Z', '59Z', '23.3Z', '12.543Z'] # greater precision that miliseconds will be ignored
    }

    pas_implicit_range = ['2016', '0638-02', '-0124-10-00', '45919-12-35T00',
                          '-72354393-00-35T15:00', '2016-02-00T23:23:00Z',
                          '0638-10-35T23:59:12.543Z']
    fail_implicit_range = ['986z', '0638-u4', '-0124-10-9', '45919-12-35T3',
                          '-72354393-00-35T15:012', '2016-02-00T23:23:7Z',
                          '0638-10-35T23:59:12.23']

    pas_explicit_range = ['[2016 TO 2020]', '[-72354393-01-31T15:00 TO 1000]',
                          '[0638-10-12T23:59:12.543Z TO 45919-12-31T00]',
                          '[* TO 2020]', '[-72354393-01-03T15:00 TO *]']
    fail_explicit_range = ['2016 TO 2020', '[-72354393-01-35T15:00 TO1000]',
                           '[0638-10-35T23:59:12.543Z TO 45919-12-35T00',
                           '2016 T 2020']
    fail_date_month = [{'year': '2200', 'month': '02', 'day': '29', 'wildcard': None },
                       {'year': '2015', 'month': '02', 'day': '29', 'wildcard': None },
                       {'year': '2015', 'month': '00', 'day': '01', 'wildcard': None },
                       {'year': '2015', 'month': '13', 'day': '01', 'wildcard': None },
                       {'year': '2015', 'month': '00', 'day': '01', 'wildcard': None },
                       {'year': '2015', 'month': '04', 'day': '31', 'wildcard': None }]

    pass_date_month = [{'year': '2016', 'month': '02', 'day': '29', 'wildcard': None},
                       {'year': '2400', 'month': '02', 'day': '29', 'wildcard': None},
                       {'year': '2015', 'month': '02', 'day': '29', 'wildcard': '*' },
                       {'year': '2015', 'month': '04', 'day': '30', 'wildcard': None },
                       {'year': '2015', 'month': '05', 'day': '31', 'wildcard': None }]

    def test_check_date_element(self):
        for typ in self.fail:
            print("FAIL date_element typ: {}".format(typ))
            for e in self.fail[typ]:
                print("FAIL date_element: {}".format(e))
                with pytest.raises(tk.Invalid):
                    SolrDaterange._check_date_element(typ, e)

        for y in self.pas:
            print("PASS date_element typ: {}".format(typ))
            for e in self.pas[typ]:
                print("PASS date_element: {}".format(e))
                assert (SolrDaterange._check_date_element(typ, e) == e)

    def test_check_implicit_range(self):
        for t in self.pas_implicit_range:
            print("PASS implicit_range: {}".format(t))
            gd = SolrDaterange._check_implicit_range(t)
            check = gd['year']
            try:
                check += '-' + gd['month']
                check += '-' + gd['day']
                check += 'T' + gd['hour']
                check += ':' + gd['minute']
                check += ':' + gd['second']
            except TypeError:
                pass
            assert(check == t)
        for t in self.fail_implicit_range:
            print("FAIL implicit: {}".format(t))
            with pytest.raises(tk.Invalid):
                SolrDaterange._check_implicit_range(t)

    def test_validate(self):
        for t in self.pas_explicit_range:
            print("PASS validate: {}".format(t))
            gd = SolrDaterange.validate(t)
        for t in self.fail_explicit_range:
            print("FAIL validate: {}".format(t))
            with pytest.raises(tk.Invalid):
                SolrDaterange.validate(t)

    def test_check_month_day_validity(self):
        for d in self.fail_date_month:
            print("FAIL month_day: {}".format(d))
            with pytest.raises(tk.Invalid):
                SolrDaterange._check_month_day_validity(d)
        for d in self.pass_date_month:
            print("PASS month_day: {}".format(d))
            res = SolrDaterange._check_month_day_validity(d)
