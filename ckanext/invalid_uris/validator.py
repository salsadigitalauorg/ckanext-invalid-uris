import ckan.plugins.toolkit as toolkit
import ckanext.invalid_uris.helpers as h
import json
import logging

from ckan.lib import helpers as core_helper
from pprint import pformat

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def validate_package(pkg_dict, uri_fields):
    u"""
    Validate uri within provided package dict.
    """

    def validate(val, f_name, entity_id, entity_type, parent_id):
        if not val:
            return

        # Build uri to validate, some fields are list (multi value).
        uri_to_validate = []

        if not core_helper.is_url(val):
            try:
                uris = json.loads(val)
                for uri in uris:
                    uri_to_validate.append(uri)
            except Exception as e:
                log.error(str(e))
            # pass
        else:
            uri_to_validate.append(val)

        # Validate each uri.
        log.debug('URIs to validate %s ' % pformat(uri_to_validate))
        for uri in uri_to_validate:
            uri_response = h.valid_uri(uri)
            _check_uri_and_update_table(uri_response, uri, f_name, entity_type, entity_id, parent_id)

    resources = pkg_dict.get('resources', [])

    # Validate package.
    for uri_field in uri_fields:
        field_name = uri_field.get('field_name')
        value = pkg_dict.get(field_name, None)
        if value is not None:
            validate(value, field_name, pkg_dict.get('id'), pkg_dict.get('type'), None)

    # Validate resources.
    for resource in resources:
        for uri_field in uri_fields:
            field_name = uri_field.get('field_name')
            value = resource.get(field_name, None)
            if value is not None:
                validate(value, field_name, resource.get('id'), 'resource', pkg_dict.get('id'))


def validate_vocabulary_service(vocab_dict):
    uri = vocab_dict.uri
    uri_response = h.valid_uri(uri)
    _check_uri_and_update_table(uri_response, uri, 'uri', 'vocabulary_service', vocab_dict.id, None)

    for term in vocab_dict.terms:
        uri = term.uri
        uri_response = h.valid_uri(uri)
        _check_uri_and_update_table(uri_response, uri, 'uri', 'vocabulary_service_term', term.id, vocab_dict.id)


def _check_uri_and_update_table(uri_response, uri, f_name, entity_type, entity_id, parent_id):
    if uri_response['valid']:
        # Remove it from invalid_uri table.
        result = get_action('delete_invalid_uri')({}, {
            'uri': uri,
            'field': f_name,
            'entity_type': entity_type
        })

        if result:
            log.debug('URI %s is valid' % pformat(uri))
        else:
            log.error('URI %s for %s (%s) is valid, but system can\'t remove it from database.' % (
                pformat(uri), pformat(entity_type), pformat(f_name)))
    else:
        # Build the data to be saved.
        get_action('create_invalid_uri')({}, {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'parent_entity_id': parent_id,
            'field': f_name,
            'uri': uri,
            'status_code': uri_response['status_code'],
            'reason': uri_response['reason']
        })
        log.error('URI %s is NOT valid %s' % (pformat(uri), pformat(uri_response)))
