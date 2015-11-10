import ckan.plugins as p
import ckan.plugins.toolkit as tk

import datetime as dt

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

def mk_field_queries(search_params):
    '''
    Customizes the fq-search-string so that query-terms
    referring to the same field (e.g. "example_field") are combined
    with logic operator taken from the value of op_<field>,
    e.g. "op_example_field". Default for this operator is "OR". op_<field>
    is removed from the querystring.
    '''
    
    fq_list = [e.split(':') for e in search_params['fq'].split()]
    operator_fields = [x for x in fq_list if x[0].startswith('op_')]
    # Assert only one operator per field
    assert (len(operator_fields) == len(set([x[0] for x in operator_fields])))
    operator_fields = dict(operator_fields)
    uniq_fields =  set([x[0] for x in fq_list if not x[0].startswith('op_')])
    querystring = ''
    for f in uniq_fields:
        try:
            operator = operator_fields['op_' + f].strip('"')
        except KeyError:
            operator = "OR"
        queryterms = [x[1] for x in fq_list if x[0] == f]
        querystring += ' '+f+':('+(' '+operator+' ').join(queryterms)+')'
        print
        print("f: {}".format(f))
        print("terms: {}".format(queryterms))
        print("qstring: {}".format(querystring))
    search_params['fq'] = querystring
    return(search_params)
            
## Needs to be put in config eventually. List of fields of
## custom searches and logical operator to apply among terms with
## the same field-name
CUSTOM_SEARCH_FIELDS = ['vocab_variables', 'vocab_system']
CUSTOM_OPS = ['op_' + field for field in CUSTOM_SEARCH_FIELDS]

class Eaw_VocabulariesPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)
    
    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        #tk.add_public_directory(config_, 'public')
        #toolkit.add_resource('fanstatic', 'eaw_vocabularies')

    # IDatasetform
    def _modify_package_schema(self, schema):
        schema.update({
            'system': [tk.get_validator('not_missing'),
                       tk.get_converter('convert_to_tags')('system')],
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
            'system': [tk.get_converter('convert_from_tags')('system'),
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
                'eaw_getnow': eaw_getnow})

    # IPackageController
    # def after_create(self, context, pkg_dict):
    #     return(pkg_dict)
    # def after_update(self, context, pkg_dict):
    #     return(pkg_dict)
    # def after_delete(self,context, pkg_dict):
    #     return(pkg_dict)
    # def after_show(self, context, pkg_dict):
    #     return(pkg_dict)
    # def after_search(self, search_results, search_params):
    #     return(search_results)
    # def before_index(self, pkg_dict):
    #     return(pkg_dict)
    # def before_view(self, pkg_dict):
    #     return(pkg_dict)
    def before_search(self, search_params):
        # the controller puts everything into the value of "fq". Extract
        # what we want to treat.
        print("INPUT search_params {}".format(search_params))
        fq = mk_field_queries(search_params)
        print("OUTPUT search_params {}".format(str(fq)))
        return(search_params)

    
