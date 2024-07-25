import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.invalid_uris.cli import get_commands
from ckanext.invalid_uris import helpers
from ckanext.invalid_uris.logic.action import create, delete, get

try:
    config_declarations = toolkit.blanket.config_declarations
except AttributeError:
    # CKAN 2.9 does not have config_declarations.
    # Remove when dropping support.
    def config_declarations(cls):
        return cls

get_action = toolkit.get_action
log = logging.getLogger(__name__)


@config_declarations
class InvalidUrisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

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
            'extract_uri_from_field': helpers.extract_uri_from_field,
            'get_invalid_uris': helpers.get_invalid_uris,
            'get_list_of_invalid_uris': helpers.get_list_of_invalid_uris,
        }

    # IActions
    def get_actions(self):
        return {
            'create_invalid_uri': create.invalid_uri,
            'delete_invalid_uri': delete.invalid_uri,
            'get_schema_uri_fields': get.schema_uri_fields,
            'get_invalid_uris': get.invalid_uris,
            'process_invalid_uris_job': create.process_invalid_uris_job,
            'register_invalid_uris_job': create.register_uri_validation_job
        }

    # IResourceController
    def before_resource_delete(self, context, resource, resources):
        context['resource'] = resource

    def after_resource_delete(self, context, resources):
        resource = context.get('resource')
        if resource and isinstance(resource, dict):
            resource_id = resource.get("id")
            log.info(f'Resource deleted {resource_id}, removing invalid uris')
            get_action('delete_invalid_uri')(context, {"entity_id": resource_id})

    # IPackageController
    def after_dataset_delete(self, context, pkg_dict):
        id = pkg_dict.get("id")
        log.info(f'Dataset deleted {id}, removing invalid uris')
        get_action('delete_invalid_uri')(context, {"entity_id": id})
        get_action('delete_invalid_uri')(context, {"parent_entity_id": id})
