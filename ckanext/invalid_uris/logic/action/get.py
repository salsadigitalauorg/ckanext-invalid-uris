import logging
import ckan.plugins.toolkit as toolkit

from ckanext.invalid_uris.model import InvalidUri
from ckanext.scheming.helpers import scheming_dataset_schemas
from ckanext.invalid_uris import jobs
from pprint import pformat

log = logging.getLogger(__name__)


def schema_uri_fields(context, config):
    u"""
    Get all fields that implement specific validator.

    :param config:
        Example value {'package_types': ['dataset', 'dataservice'], 'validator': 'qdes_uri_validator'}
    """
    uri_fields = []
    schemas = scheming_dataset_schemas()

    for dataset_type in schemas:
        schema_fields = []
        if dataset_type in config.get('package_types'):
            dataset_fields = schemas[dataset_type].get('dataset_fields')
            resource_fields = schemas[dataset_type].get('resource_fields', None)

            schema_fields = dataset_fields + resource_fields if resource_fields else dataset_fields

        for field in schema_fields:
            if config.get('validator') in field.get('validators', '').split():
                if not field.get('field_name') in uri_fields:
                    uri_fields.append(field.get('field_name'))

    return uri_fields


def invalid_uris(context, data_dict):
    u"""
    Get Invalid URI's

    :param data_dict: has the following keys:
        Example value {'uri': 'http://example.com', 'field': 'uri', 'entity_id': dataset_id, 'parant_entity_id':'')
    """

    # TODO: Who should have access to this action? toolkit.check_access(?)
    return [invalid_uri.as_dict() for invalid_uri in InvalidUri.filter(data_dict)]


@toolkit.side_effect_free
def process_invalid_uris(context, data_dict):
    toolkit.check_access('sysadmin', context)
    entity_types = data_dict.get('entity_types', 'dataset dataservice resource')
    try:
        jobs.process_invalid_uris(entity_types.split())
        return 'Successfully submitted process_invalid_uris job'
    except Exception as e:
        log.error(e)
        return 'Failed to process_invalid_uris job: {}'.format(e)
