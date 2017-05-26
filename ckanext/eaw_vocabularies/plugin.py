from pylons import c
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckanext.eaw_vocabularies.validate_solr_daterange as dr
from ckantoolkit import h

import datetime as dt
import re

## Needs to be put in config eventually. List of fields of
## custom searches and logical operator to apply among terms with
## the same field-name
CUSTOM_SEARCH_FIELDS = ['variables', 'systems']
CUSTOM_OPS = ['OP_' + field for field in CUSTOM_SEARCH_FIELDS]

# template helper functions
def eaw_choices(fieldname, dataset_type):
    '''Returns the list of choices fieldname in from scheming_schema'''
    options = tk.get_action('scheming_dataset_schema_show')(
        {}, {'type': dataset_type, 'expanded': False})
    options = [x.get('choices') for x in options.get('dataset_fields')
               if x.get('field_name') == fieldname][0]
    return(options)
 
def eaw_getnow():
    ''' Current date in ISO 8601'''
    return(dt.date.today().isoformat())

def eaw_get_facetfields():
    '''Returns (name, value) list of facet_fields'''
    facetfields = [f for f in tk.c.fields if f[0] in tk.c.facet_titles.keys()]
    return(facetfields)

def eaw_get_facetnames():
    return(list(set([ff[0] for ff in eaw_get_facetfields()])))

def eaw_mk_fields_grouped():
    ''' c.fields_grouped are only provided by package-controller,
    not by group-controller. So we do it ourselves.'''
    
    fields_grouped = {}
    for f in tk.c.fields:
        try:
            fields_grouped[f[0]].append(f[1])
        except KeyError:
            fields_grouped[f[0]] = [f[1]]
    return fields_grouped

#def mk_field_queries(search_params, vocabfields):
def mk_field_queries(search_params):
    '''
    Customizes the fq-search-string so that query-terms
    referring to the same <field> (e.g. "example_field") are combined
    with logic operator taken from the value of OP_<field>,
    e.g. "OP_example_field". Default for this operator is "AND" to
    keep compatibility. The other possible value is "OR".
    OP_<field> is removed from the querystring.
    '''

    def _operator(fn, operator_fields):
        ''' Returns boolean operator with which to connect
        sear-terms in field <fn>'''
        try:
            operator = operator_fields['OP_' + fn].strip('"')
        except KeyError:
            operator = "AND"
        return(operator)

    # def _prefix(fn):
    #     return("vocab_"+fn if fn in vocabfields else fn)

    def _fix_timestamp(tstamp):
        return(tstamp + "Z" if len(tstamp.split(":")) == 3 else tstamp)

    def _vali_daterange(trange):
        print("_valid_daterange trange: {}".format(trange))
        try:
            trange = dr.SolrDaterange.validate(trange)
        except dr.Invalid as e:
            print("VALIDATION FAILED")
            c.search_errors = {'timerange': str(e)}
        return(trange)

    def _assemble_timerange(fqd):
        ''' 
        Produce a DaterangeField compatible search string
        from timestart and timeend.
        '''

        try:
            fqd["timestart"] = _fix_timestamp(fqd["timestart"].strip('"'))
        except KeyError:
            try:
                fqd["timeend"] = _fix_timestamp(fqd["timeend"].strip('"'))
            except KeyError:
                return(fqd)
            else:

                fqd["timerange"] = "[* TO " + fqd["timeend"] + "]"
                fqd["timerange"] = _vali_daterange(fqd["timerange"])
                return(fqd)
        else:
            try:
                fqd["timeend"] = _fix_timestamp(fqd["timeend"].strip('"'))
            except KeyError:
                fqd["timerange"] = fqd["timestart"]
                fqd["timerange"] = _vali_daterange(fqd["timerange"])
                return(fqd)
            else:
                fqd["timerange"] = ("[" + fqd["timestart"] + " TO "
                                    + fqd["timeend"] + "]")
                fqd["timerange"] = _vali_daterange(fqd["timerange"])
                return(fqd)
            
    def _collect_fqfields(queryfield):
        querystring = search_params.get(queryfield, '')
        querystring = re.sub(": +", ":", querystring)
        ## split querystring at spaces if space doesn't occur in quotes
        ## http://stackoverflow.com/a/2787064
        pat = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
        splitquery = pat.split(querystring)[1::2]
        querylist = [e.split(':', 1) for e in splitquery]
        # extract operator_fields
        operator_fields = dict([x for x in querylist if x[0].startswith('OP_')])
        # extract eaw_fqfields
        fq_list_eaw = [x for x in querylist if x[0].startswith('eaw_fqfield_')]
        # remove fqfields from query
        querylist = [x for x in querylist if not x[0].startswith('eaw_fqfield_')]
        # remove OP_* fields from query
        querylist = [f for f in querylist if not 'eaw_fqfield_' in f[0]]
        # remove the prefix / infix
        fq_list_eaw = [[x[0].replace('eaw_fqfield_', ''), x[1]]
                       for x in fq_list_eaw]
        operator_fields = {x[0].replace('eaw_fqfield_', ''): x[1]
                           for x in operator_fields.items()}
        return((querylist, fq_list_eaw, operator_fields))

    
    fq_list_orig, fq_list_eaw, operator_fields = _collect_fqfields('fq')
    q_list_orig, fq_list_eaw_q, operator_fields_q = _collect_fqfields('q')
    fq_list_eaw.extend(fq_list_eaw_q)
    operator_fields.update(operator_fields_q)

    # build pre-query-strings
    fq_dict = {}
    for f in fq_list_eaw:
        try:
            fq_dict[f[0]] += ' '+_operator(f[0], operator_fields)+' '+f[1]
        except KeyError:
            fq_dict[f[0]] = f[1]
    fq_dict = _assemble_timerange(fq_dict)
    fq_dict.pop("timestart", None)
    fq_dict.pop('timeend', None)
    # assemble fq-query-string
    fq_query = ''
    for f in fq_dict.items():
        fq_query += ' ' + f[0] + ':(' + f[1] + ')'
    for f in fq_list_orig:
        fq_query += ' ' + f[0] + ':(' + f[1] + ')'
    # re-assemble q-query-string
    q_query = ''
    for f in q_list_orig:
        q_query += ' ' + f[0]
        try:
            q_query += ':'+f[1]
        except IndexError:
            pass
    search_params['fq'] = fq_query
    search_params['q'] = q_query
    return(search_params)    
            
class Eaw_VocabulariesPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)
        
    # ITemplateHelpers
    def get_helpers(self):
        return({'eaw_choices': eaw_choices,
                'eaw_getnow': eaw_getnow,
                'eaw_get_facetfields': eaw_get_facetfields,
                'eaw_get_facetnames': eaw_get_facetnames,
                'eaw_mk_fields_grouped':eaw_mk_fields_grouped
        })

    # IPackageController
    def before_search(self, search_params):
        sp = mk_field_queries(search_params)
        return(sp)


    
