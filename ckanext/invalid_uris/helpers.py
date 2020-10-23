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


def get_contact_point_data(contact_point_url):

    # TODO: Once this story has been implemented https://it-partners.atlassian.net/browse/DDCI-41 use the action to retrieve contact point data
    # data_dict = get_action('')({}, {'url':contact_point_url})
    point_of_contacts = [
        {
            'Name': 'Scott Lutwyche',
            'Functional Postition': 'Solutions Architect',
            'Email': 'scott.lutwyche@des.qld.gov.au',
            'Url': 'http://linked.data.gov.au/def/iso19115-1/RoleCode/author'
        },
        {
            'Name': 'Viraj Ubayasiri',
            'Functional Postition': 'Senior Business Analyst',
            'Email': 'viraj.ubayasiri@des.qld.gov.au',
            'Url': 'http://linked.data.gov.au/def/iso19115-1/RoleCode/coAuthor'
        },
        {
            'Name': 'Kelly Bryant',
            'Functional Postition': 'Senior Scientist (Modelling), Soil & Land Resources',
            'Email': 'kelly.bryant@des.qld.gov.au',
            'Url': 'http://linked.data.gov.au/def/iso19115-1/RoleCode/publisher'
        },
        {
            'Name': 'Daniel Brough',
            'Functional Postition': 'Science Leader, Science Information Services',
            'Email': 'daniel.brough@des.qld.gov.auu',
            'Url': 'http://linked.data.gov.au/def/iso19115-1/RoleCode/custodian'
        }
    ]

    point_of_contact = next((point_of_contact for point_of_contact in point_of_contacts if point_of_contact.get('Url') == contact_point_url), None)
    log.debug('point_of_contact: {}'.format(point_of_contact))
    return point_of_contact
