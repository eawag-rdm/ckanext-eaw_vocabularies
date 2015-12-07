from dateval import *

def test_split_explicit_range():
    calibration = [('jsagdh', 'kjsd8'), ('jsdgh', ), ('2016-12-01:02:03.55', ),
                   ('2016-12-01:02:03.55', '2016-12-01:02:03.56.456')]
    res = []
    for teststr in ["jsagdh TO kjsd8", "jsdgh", "2016-12-01:02:03.55",
                    "2016-12-01:02:03.55 TO 2016-12-01:02:03.56.456"]:
        res.append(SolrDaterange._split_explicit_range(teststr))
    assert (res == calibration)

def test_timestamp_fail():
    timetest_err = ['', '0', '02:', ':04', '25', '02:2', '03:60', '3:12Z',
                    '03:59:','03:59:3Z', '04:48:967Z', '07:32:59.',
                    '24:07:00Z', '24:00:00.005Z']
    datetest_err = ['2014-02-29', '2300-02-29',  '01232-01-31',
                    '-08765-12-31', '2016-32-03', '-987658-00-07',
                    '87654-08-00']
    testts = ([x + 'T23:59:58.9997Z' for x in datetest_err] +
              ['2015-11-30T' + x for x in timetest_err])
    for t in testts:
        print("TIMESTAMP: {}".format(t))
        try:
            SolrDaterange.validate(t)
        except Invalid:
               pass
        else:
               raise Exception("{} should fail".format(t))

def test_timestamp_pass():
    timetest_ok = ['01:00', '00','15:44:49.98Z', '04', '05:12',
                   '17:54:12', '24', '24:00:00Z', '23:12:18.986754Z',
                   '15:44:49.98']
    
    datetest_ok = ['2400-02-29', '2014-02-28', '0023', '0435-12', '-0987-05-31']

    dateonly_ok = ['2016', '-0999-12', '59867-03-01']

    testts = ([x + 'T23:59:58.9997Z' for x in datetest_ok] +
              ['2015-11-30T' + x for x in timetest_ok] +
              dateonly_ok)
    for t in testts:
            SolrDaterange.validate(t)

def test_daterange_pass():
    rangetest_ok = ['2015 TO 2018', '* TO 2018-12-04', '*', '* TO *', 
                    '0900 TO *', '3012-12-31T12:01:03.765Z TO 3014']
    for t in rangetest_ok:
        SolrDaterange.validate(t)

def test_daterange_fail():
    rangetest_err = ['2015TO 2018', '* TO2018-12-04', '* ', '* to *',
                    '0900 *', '3012-12-31Z12:01:03.765 T 3014']
    for t in rangetest_err:
        try:
            SolrDaterange.validate(t)
        except Invalid:
            pass
        else:
            raise Exception("{} should fail".format(t))

