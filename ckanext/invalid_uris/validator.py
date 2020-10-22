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


def is_value_exist(id, entity):
    u"""
    Return True if the value is still in the entity.
    In some case, user maybe delete the invalid value on edit after the background job run,
    that will leave the invalid_uri data outdated, so here we will delete it as well.
    """
    uris = Session.query(InvalidUri).filter(InvalidUri.id == id).all()
    invalid_uris = [uri.as_dict() for uri in uris]
    remove = False

    for uri in invalid_uris:
        entity_type = uri.get('entity_type', None)
        # Load entity.
        if entity_type == 'vocabulary_service':
            # @todo: add the check for this entity.
            pass
        elif entity_type == 'vocabulary_service_term':
            # @todo: add the check for this entity.
            pass
        else:
            # Load package.
            pkg_dict = entity
            resources = pkg_dict.get('resources', [])

            # Get the value from the entity.
            if entity_type == 'resource':
                current_resource_entity = []
                for resource in resources:
                    if resource.get('id') == uri.get('entity_id'):
                        current_resource_entity = resource

                value = current_resource_entity.get(uri.get('field'))
            else:
                value = pkg_dict.get(uri.get('field'))

            # If the value is empty, let's remove it from invalid_uri table.
            if not value:
                remove = True

            # Check if the entity value same as invalid uri on table.
            if not uri.get('uri') in h.extract_uri_from_field(value):
                remove = True

        if remove:
            get_action('delete_invalid_uri')({}, {
                'uri': uri.get('uri'),
                'field': uri.get('field'),
                'entity_type': entity_type
            })
            return False

    return True


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
