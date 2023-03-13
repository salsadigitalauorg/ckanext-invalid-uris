import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.invalid_uris.cli import get_commands
from ckanext.invalid_uris import helpers
from ckanext.invalid_uris.logic.action import create, delete, get

get_action = toolkit.get_action
log = logging.getLogger(__name__)


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
    def before_delete(self, context, resource, resources):
        # Set resource in context so it can be used in the IResourceController `after_delete interface` below
        context['resource'] = resource

    # IResourceController & IPackageController
    def after_delete(self, context, pkg_dict_or_resources):
        try:
            # This interface can be called from either IResourceController & IPackageController
            # Should be resolved in a future release https://github.com/ckan/ckan/pull/6501
            # We need to find which interface is being called
            # get_endpoint works fine from a UI request but from the API we need use the request.path because get_endpoint returns ('google_analytics', 'action')
            endpoint = toolkit.get_endpoint() if toolkit.request and toolkit.request.endpoint else ('', '')
            path = toolkit.request.path if toolkit.request else ''
            resource = context.get('resource')
            if (endpoint == ('resource', 'delete') or path.endswith('resource_delete')) and isinstance(resource, dict):
                id = resource.get('id')
                log.info(f'Resource deleted {id}, removing invalid uris')
                get_action('delete_invalid_uri')(context, {"entity_id": id})
            elif (endpoint == ('dataset', 'delete') or path.endswith('package_delete')) and isinstance(pkg_dict_or_resources, dict):
                id = pkg_dict_or_resources.get("id")
                log.info(f'Dataset deleted {id}, removing invalid uris')
                get_action('delete_invalid_uri')(context, {"entity_id": id})
                get_action('delete_invalid_uri')(context, {"parent_entity_id": id})
        except Exception as ex:
            log.error(ex)
