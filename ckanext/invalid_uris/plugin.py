import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.invalid_uris.cli import get_commands
from ckanext.invalid_uris import helpers
from ckanext.invalid_uris.logic.action import create, delete, get


class InvalidUrisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'invalid_uris')

    # IClick
    def get_commands(self):
        return get_commands()

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'valid_uri': helpers.valid_uri,
            'extract_uri_from_field': helpers.extract_uri_from_field
        }

    # IActions
    def get_actions(self):
        return {
            'create_invalid_uri': create.invalid_uri,
            'delete_invalid_uri': delete.invalid_uri,
            'get_schema_uri_fields': get.schema_uri_fields,
            'get_invalid_uris': get.invalid_uris,
            'process_invalid_uris_job': create.process_invalid_uris_job
        }
