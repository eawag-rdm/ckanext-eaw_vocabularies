from ckan.plugins.toolkit import Invalid
import re

class SolrDaterange(object):
    '''Evaluates wheter a date-time string conforms to
    the DateRangeField specification of SOLR 5.4.
    https://cwiki.apache.org/confluence/display/solr/Working+with+Dates
    '''
    
    dateregex = '^(?P<year>-?\d{4,})(-(?P<month>\d{2})(-(?P<day>\d{2}))?)?$|^(?P<wildcard>\*)$'
    timeregex = '^(?P<hours>\d{2})(:(?P<mins>\d{2})(:(?P<secs>\d{2}(\.\d+)?Z?))?)?$'
    expli_dateregex = '^(?P<start>.*) TO (?P<end>.*)$'

    @classmethod
    def _split_explicit_range(cls, datestr):
        ''' Splits explicit range (containing "TO") into two
        implicit range fields'''
        m = re.match(cls.expli_dateregex, datestr)
        if m:
            return((m.groupdict()['start'], m.groupdict()['end']))
        else:
            return((datestr,))

    @classmethod
    def _split_dt(cls, datestr):
        try:
            dat, tim = datestr.split('T')
            if tim == '':
                raise Invalid("{} is not a valid date".format(datestr))
        except ValueError:
            dat = datestr.split('T')[0]
            tim = ''
        return((dat, tim))

    @classmethod
    def _val_date(cls, dat):
        m = re.match(cls.dateregex, dat)
        if not m:
            raise Invalid("{} is not a valid date".format(dat))
        return(m.groupdict())

    @classmethod
    def _val_month_day(cls, datedict):
        if datedict['wildcard'] == '*':
            return('*')
        intyear = int(datedict['year'])
        v_date = datedict['year']
        try:
            intmonth = int(datedict['month'])
            v_date += "-" + datedict['month']
        except TypeError:
            intmonth = None
        try:
            intday = int(datedict['day'])
            v_date += "-" + datedict['day']
        except TypeError:
            intday = None
        if ((datedict['year'].startswith('0') and len(datedict['year'])) > 4 or
            (datedict['year'].startswith('-0') and len(datedict['year'])) > 5):
            raise Invalid("{} is not a valid year.".format(datedict['year']))
        noleapyear = intyear % 4 != 0 or (intyear % 100 == 0
                                          and intyear % 400 != 0)
        maxdays = [31, 28 if noleapyear else 29, 31, 30, 31, 30, 31, 31, 30, 31,
                   30, 31]
        if not (intmonth is None or 1 <= intmonth <= 12):
            raise Invalid("{} is not a valid month.".format(datedict['month']))
        if not (intday is None or 1 <= intday <= maxdays[intmonth - 1]):
            raise Invalid("{} is not a valid day.".format(datedict['day']))
        return(v_date)

        
    @classmethod
    def _valtime(cls, tim):
        m = re.match(cls.timeregex, tim)
        if not m:
            raise Invalid("{} is not a valid time.".format(tim))
        return(m.groupdict())
    
    @classmethod
    def _valhour_min_sec(cls, timedict):
        inthour = int(timedict["hours"])
        v_time = timedict["hours"]
        try:
            intmins = int(timedict["mins"])
            v_time += ":" + timedict["mins"]
        except TypeError:
            intmins = None;
        secs = timedict["secs"]
        if secs is None:
            intsecs = None
        else:
            if secs[-1] != "Z":
                intsecs = float(secs)
            else:
                intsecs = float(secs[0:-1])
                v_time += ":" + secs
        if inthour == 24 and ((intmins > 0 and not intmins is None) or
                              (intsecs > 0 and not intsecs is None)):
            raise Invalid("{} is not a valid hour".format(timedict["hours"]))
        if inthour >= 25:
            raise Invalid("{} is not a valid hour".format(timedict["hours"]))
        if intmins is not None and not (0 <= intmins <= 59):
            raise Invalid("{} are not valid minutes".format(timedict["mins"]))
        if intsecs is not None and not (0 <= intsecs < 60.):
            raise Invalid("{} are not valid seconds".format(timedict["secs"]))
        return(v_time)
 
    @classmethod
    def validate(cls, datestr):
        valid = []
        dates = cls._split_explicit_range(datestr)
        for timestamp in dates:
            dat, tim = cls._split_dt(timestamp)
            valid.append(cls._val_month_day(cls._val_date(dat)))
            if tim:
                v_time = cls._valhour_min_sec(cls._valtime(tim))
                valid[-1] += 'T' + v_time
        if len(valid) == 2:
            valid = "[" + valid[0] + " TO " + valid[1] + "]"
        elif len(valid) == 1:
            valid = valid[0]
        else:
            raise Invalid("Something went horribly wrong.")
        return(valid)
            

