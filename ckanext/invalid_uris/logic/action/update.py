import logging

from datetime import datetime
from ckanext.invalid_uris.model import InvalidUri
from pprint import pformat

log = logging.getLogger(__name__)


def delete_invalid_uri(context, data):
    u"""
    Delete the invalid uri from table, can be filtered by uri, field name, and entity type.

    :param data:
        Example value {'uri': 'http://google.com', 'field': 'field_name', 'entity_type': 'resource'}
    """
    try:
        invalid_uri_data = InvalidUri.filter(data)

        for invalid_uri in invalid_uri_data:
            invalid_uri.delete()
            invalid_uri.commit()

        return True
    except Exception as e:
        return False
