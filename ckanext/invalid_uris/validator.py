import ckan.plugins.toolkit as toolkit
import ckanext.invalid_uris.helpers as h
import json
import logging

from ckan.lib import helpers as core_helper
from ckan.model import Session
from ckanext.invalid_uris.model import InvalidUri
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
        uri_to_validate = h.extract_uri_from_field(val)

        # Delete URI's that do not exist any more for this field
        _remove_invalid_uri_orphans(f_name, entity_id, parent_id, uri_to_validate)

        # Validate each uri.
        log.debug('URIs to validate field: %s value: %s ' % (pformat(f_name), pformat(uri_to_validate)))
        for uri in uri_to_validate:
            uri_response = h.valid_uri(uri)
            _check_uri_and_update_table(uri_response, uri, f_name, entity_type, entity_id, parent_id)

    resources = pkg_dict.get('resources', [])
    extras = pkg_dict.get('extras', [])

    # Validate package.
    log.debug('================================================')
    log.debug('Validating package: %s (id: %s)' % (pkg_dict.get('title'), pkg_dict.get('id')))
    log.debug('================================================')
    for field_name in uri_fields:
        value = pkg_dict.get(field_name, None)
        if value is not None:
            validate(value, field_name, pkg_dict.get('id'), pkg_dict.get('type'), None)

        # Validate package extra.
        value = extras.get(field_name, None)
        if value is not None:
            validate(value, field_name, pkg_dict.get('id'), pkg_dict.get('type'), None)

    # Validate resources.
    for resource in resources:
        log.debug('================================================')
        log.debug('Validating resource: %s (id: %s)' % (resource.get('name'), resource.get('id')))
        log.debug('================================================')

        for field_name in uri_fields:
            value = resource.get(field_name, None)
            if value is not None:
                validate(value, field_name, resource.get('id'), 'resource', pkg_dict.get('id'))

    log.debug('================================================')
    log.debug(' ')


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
            'entity_type': entity_type,
            'entity_id': entity_id,
            'parent_entity_id': parent_id
        })

        if result:
            log.debug('URI %s is valid and successfully removed from database' % pformat(uri))
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


def _remove_invalid_uri_orphans(f_name, entity_id, parent_id, uri_to_validate):
    current_field_invalid_uris = get_action('get_invalid_uris')({}, {'field': f_name, 'entity_id': entity_id, 'parent_entity_id': parent_id})
    for invalid_uri in [invalid_uri for invalid_uri in current_field_invalid_uris if invalid_uri.get('uri', None) not in uri_to_validate]:
        result = get_action('delete_invalid_uri')({}, invalid_uri)

        if result:
            log.debug('Removed orphan URI {0} {1} {2} successfully'.format(
                invalid_uri.get('uri', None), parent_id or entity_id, f_name))
        else:
            log.error('Failed to remove orphan {0} {1} {2} successfully'.format(
                invalid_uri.get('uri', None), parent_id or entity_id, f_name))
