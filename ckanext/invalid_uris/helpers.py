import requests
import ckan.plugins.toolkit as toolkit
import logging
import json
import time

from ckan.lib import helpers as core_helper
from ckan.model import Session
from ckanext.invalid_uris.model import InvalidUri

get_action = toolkit.get_action
config = toolkit.config
log = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()


def valid_uri(uri, retries=0, method='head'):
    u"""
    Check if the given uri is valid or not.
    """
    response = None
    result = None
    proxies = None
    headers = None
    proxy = config.get('ckanext.invalid_uris.proxy')
    timeout = config.get('ckanext.invalid_uris.timeout', 10)
    user_agent = config.get('ckanext.invalid_uris.user_agent')
    verify_certificate = config.get('ckanext.invalid_uris.verify_certificate', True)
    retry_attempts = config.get('ckanext.invalid_uris.retry_attempts', 3)
    
    try:
        if proxy:
            proxies = {
                'http': proxy,
                'https': proxy,
            }
        if user_agent:
            headers = {
                "User-Agent": user_agent
            }
        response = requests.request(
            method=method,
            url=uri,
            headers=headers,
            verify=verify_certificate,
            timeout=timeout,
            proxies=proxies,
            allow_redirects=True,
        )
        # If the head method is not allowed then try with get method.
        if response is not None and response.status_code == 405 and method == 'head':
            log.warning(f'Method {method} not allowed for uri {uri}')
            result = valid_uri(uri, retries, 'get')
        else:
            result = {
                'valid': response.ok,
                'status_code': response.status_code,
                'reason': response.reason,
                'response': response
            }
    except (requests.RequestException, requests.ConnectionError, requests.HTTPError) as e:
        log.error(f'Request exception: {e}')
        if retries <= retry_attempts:
            log.warning(f'Retry attempt {retries} for uri {uri}')
            retries = retries+1
            time.sleep(retries)
            result = valid_uri(uri, retries)
        else:
            result = {
                'valid': False,
                'status_code': response.status_code if response is not None else '',
                'reason': response.reason if response is not None else str(e),
                'response': response
            }
    except Exception as e:
        result = {
            'valid': False,
            'status_code': response.status_code if response is not None else '',
            'reason': response.reason if response is not None else str(e),
            'response': response
        }

    return result


def extract_uri_from_field(value):
    u"""
    Extract uris from single/multi value field.
    """
    extracted_uris = []
    if not core_helper.is_url(value):
        try:
            extracted_uris = json.loads(value)
        except Exception as e:
            log.warning('Error in extract_uri_from_field: {}'.format(e))
            return extracted_uris
    else:
        extracted_uris.append(value)

    uri_domain_whitelist = toolkit.aslist(config.get('ckanext.invalid_uris.domain_whitelist'))
    if uri_domain_whitelist:
        # Only check uris with domains on the whitelist
        for index, extracted_uri in enumerate(extracted_uris):
            uri_domain_valid = False
            for uri_domain in uri_domain_whitelist:
                if uri_domain in extracted_uri:
                    uri_domain_valid = True
                    break
            if not uri_domain_valid:
                log.debug(f'Removing uri {extracted_uri} because it is not part of the valid domain whitelist {uri_domain_whitelist}')
                extracted_uris.pop(index)

    return extracted_uris


def get_invalid_uris(entity_id):
    u"""
    Get invalid uris for the current package.
    """
    uris = Session.query(InvalidUri).filter(InvalidUri.entity_id == entity_id).all()

    return [uri.as_dict() for uri in uris]


def get_list_of_invalid_uris():
    """
    Helper function to return a list of entities that have invalid uri.
    """
    # Get list of invalid uris.
    invalid_uris = Session.query(InvalidUri).all()

    # Build package list.
    entities = {}
    for uri in invalid_uris:
        if uri.entity_id in entities:
            entities[uri.entity_id]['fields'].append(uri.field)
        else:
            entities[uri.entity_id] = {
                'type': uri.entity_type,
                'fields': [uri.field],
            }

    return entities
