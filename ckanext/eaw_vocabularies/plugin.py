from pylons import c
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckanext.eaw_vocabularies.validate_solr_daterange as dr

import datetime as dt
import re

## Needs to be put in config eventually. List of fields of
## custom searches and logical operator to apply among terms with
## the same field-name
CUSTOM_SEARCH_FIELDS = ['variables', 'systems']
CUSTOM_OPS = ['OP_' + field for field in CUSTOM_SEARCH_FIELDS]

# template helper functions
def eaw_taglist(vocab_name, pad=False):
    tag_list = tk.get_action('tag_list')
    tags = tag_list(data_dict={'vocabulary_id': vocab_name})
    tags = [{'value': tag} for tag in tags]
    if pad:
        tags = [{'value': ' '}] + tags
    return(tags)

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
        except AttributeError:
            fields_grouped[f[0]] = [fields_grouped[f[0]], f[1]]
        except KeyError:
            fields_grouped[f[0]] = f[1]
    return(fields_grouped)

def mk_field_queries(search_params, vocabfields):
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

    def _prefix(fn):
        return("vocab_"+fn if fn in vocabfields else fn)

    def _fix_timestamp(tstamp):
        return(tstamp + "Z" if len(tstamp.split(":")) == 3 else tstamp)

    def _fix_timefields(d):
        c.fields = [x for x in c.fields if x[0] not in ['timestart', 'timeend']]

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
                _fix_timefields({'timestart': "*", 'timeend': fqd["timeend"]}) 
                return(fqd)
        else:
            try:
                fqd["timeend"] = _fix_timestamp(fqd["timeend"].strip('"'))
            except KeyError:
                fqd["timerange"] = fqd["timestart"]
                fqd["timerange"] = _vali_daterange(fqd["timerange"])
                _fix_timefields({'timestart': fqd["timestart"]}) 
                return(fqd)
            else:
                fqd["timerange"] = ("[" + fqd["timestart"] + " TO "
                                    + fqd["timeend"] + "]")
                fqd["timerange"] = _vali_daterange(fqd["timerange"])
                _fix_timefields({'timestart': fqd["timestart"],
                                 'timeend': fqd["timeend"]})
                return(fqd)
            
    def _collect_fqfields(queryfield):
        querystring = search_params.get(queryfield, '');
        querystring = re.sub(": +", ":", querystring)
        querylist = [e.split(':', 1) for e in querystring.split()]
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
        fq_query += ' ' + _prefix(f[0]) + ':(' + f[1] + ')'
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
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)
    
    # We need a list of all vocabulary fields
    _vocab_fields = [v['name'] for v in tk.get_action('vocabulary_list')()]
    
    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        #tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'eaw_vocabularies')
    # IDatasetform
    def _modify_package_schema(self, schema):
        schema.update({
            'systems': [tk.get_validator('not_missing'),
                       tk.get_converter('convert_to_tags')('systems')],
            'variables': [tk.get_validator('not_missing'),
                          tk.get_converter('convert_to_tags')('variables')],
            'timerange': [tk.get_validator('not_missing'),
                          tk.get_converter('convert_to_extras')]
        })
        return(schema)
        
    def create_package_schema(self):
        schema = super(Eaw_VocabulariesPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return(schema)

    def update_package_schema(self):
        schema = super(Eaw_VocabulariesPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return(schema)

    def show_package_schema(self):
        schema = super(Eaw_VocabulariesPlugin, self).show_package_schema()
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'systems': [tk.get_converter('convert_from_tags')('systems'),
                       tk.get_validator('ignore_missing')],
            'variables': [tk.get_converter('convert_from_tags')('variables'),
                          tk.get_validator('ignore_missing')],
            'timerange': [tk.get_converter('convert_from_extras'),
                          tk.get_validator('ignore_missing')]
        })
        return(schema)
    
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []
    
    # ITemplateHelpers
    def get_helpers(self):
        return({'eaw_taglist': eaw_taglist,
                'eaw_getnow': eaw_getnow,
                'eaw_get_facetfields': eaw_get_facetfields,
                'eaw_get_facetnames': eaw_get_facetnames,
                'eaw_mk_fields_grouped':eaw_mk_fields_grouped
        })

    # IPackageController
    def before_search(self, search_params):
        print("before_search - input: search_params")
        print(search_params)
        sp = mk_field_queries(search_params, self._vocab_fields)
        print("before_search - output: search_params")
        print(sp)
        # print("before_search - facetfields:")
        # print(eaw_get_facetfields())
        return(sp)

    
