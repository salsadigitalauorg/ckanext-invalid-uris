import requests
import ckan.plugins.toolkit as toolkit
import logging

from pprint import pformat

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def valid_uri(uri):
    u"""
    Check if the given uri is valid or not.
    """
    r = None
    try:
        r = requests.options(uri)
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
