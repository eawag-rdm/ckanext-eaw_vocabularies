import ckan.plugins as p
import ckan.plugins.toolkit as tk




class Eaw_VocabulariesPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IConfigurer)
    p.implements(p.IDatasetForm)
    
    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        #toolkit.add_resource('fanstatic', 'eaw_vocabularies')

    # IDatasetform
    def create_package_schema(self):
        schema = super(Eaw_VocabulariesPlugin, self).create_package_schema()
        schema.update({
            'System': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')]
            })
        return(schema)
