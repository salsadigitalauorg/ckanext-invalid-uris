import logging

from datetime import datetime
from ckanext.invalid_uris.model import InvalidUri
from pprint import pformat

log = logging.getLogger(__name__)


def invalid_uri(context, data):
    u"""
    Save invalid uri value to database.
    """
    session = context['session']
    uri = data.get('uri', '')

    current_data = InvalidUri.filter({
        'uri': uri,
        'field': data.get('field', ''),
        'entity_type': data.get('entity_type', '')
    })

    if len(current_data) == 0:
        # If uri is not exist, then create it.
        invalid_uri_data = InvalidUri(
            entity_type=data.get('entity_type', ''),
            entity_id=data.get('entity_id', ''),
            parent_entity_id=data.get('parent_entity_id', ''),
            field=data.get('field', ''),
            uri=uri,
            status_code=data.get('status_code', ''),
            reason=data.get('reason', '')
        )
        session.add(invalid_uri_data)
        session.commit()
    else:
        # Otherwise edit it.
        for invalid_uri_data in current_data:
            for key in data:
                setattr(invalid_uri_data, key, data.get(key))

            # Update date_last_checked.
            setattr(invalid_uri_data, 'date_last_checked', datetime.utcnow())

            # Save the updated data.
            invalid_uri_data.save()

    return True
