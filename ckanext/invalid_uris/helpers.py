import requests
import ckan.plugins.toolkit as toolkit
import logging

from ckanext.invalid_uris.validator import validate_package, validate_vocabulary_service
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


def test():
    # Load package
    pkg_dict = get_action('get_vocabulary_service')({}, 'classification')

    validate_vocabulary_service(pkg_dict)
