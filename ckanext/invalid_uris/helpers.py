import requests
import ckan.plugins.toolkit as toolkit
import logging
import json

from ckan.lib import helpers as core_helper
from pprint import pformat

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def valid_uri(uri):
    u"""
    Check if the given uri is valid or not.
    """
    r = None
    try:
        r = requests.get(uri)
        response = {
            'valid': False if r.status_code != 200 else True,
            'status_code': r.status_code,
            'reason': r.reason
        }
    except Exception as e:
        response = {
            'valid': False,
            'status_code': r.status_code if r is not None else '',
            'reason': r.reason if r is not None else str(e)
        }

    return response


def extract_uri_from_field(value):
    u"""
    Extract uris from single/multi value field.
    """
    extracted_uris = []
    if not core_helper.is_url(value):
        try:
            extracted_uris = json.loads(value)
        except Exception as e:
            log.error('Error in extract_uri_from_field: {}'.format(e))
            return extracted_uris
    else:
        extracted_uris.append(value)

    return extracted_uris
