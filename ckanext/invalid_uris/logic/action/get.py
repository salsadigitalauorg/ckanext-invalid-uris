import logging

from ckanext.invalid_uris.model import InvalidUri
from ckanext.scheming.helpers import scheming_dataset_schemas
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
        package_fields = []
        if dataset_type in config.get('package_types'):
            package_fields = schemas[dataset_type].get('dataset_fields') + schemas[dataset_type].get(
                'resource_fields')

        for field in package_fields:
            if config.get('validator') in field.get('validators', '').split():
                if not field.get('field_name') in uri_fields:
                    uri_fields.append(field.get('field_name'))

    return uri_fields
