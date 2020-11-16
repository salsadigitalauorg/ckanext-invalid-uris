import logging
import ckan.plugins.toolkit as toolkit

from datetime import datetime
from ckanext.invalid_uris.model import InvalidUri
from ckanext.invalid_uris import jobs
from pprint import pformat

log = logging.getLogger(__name__)


def invalid_uri(context, data):
    u"""
    Save invalid uri value to database.
    """
    session = context['session']
    uri = data.get('uri', '')

    current_data = InvalidUri.filter(data)

    if len(current_data) == 0:
        # If uri is not exist, then create it.
        invalid_uri_data = InvalidUri(**data)
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


@toolkit.side_effect_free
def process_invalid_uris_job(context, data_dict):
    toolkit.check_access('sysadmin', context)
    entity_types = data_dict.get('entity_types', 'dataset dataservice resource')
    try:
        jobs.process_invalid_uris(entity_types.split())
        return 'Successfully submitted process_invalid_uris job'
    except Exception as e:
        log.error(e)
        return 'Failed to process_invalid_uris job: {}'.format(e)
