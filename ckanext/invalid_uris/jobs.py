import logging
import ckan.plugins.toolkit as toolkit

from datetime import datetime, timedelta
from ckan.model import Session
from ckan.model.package import Package
from ckanext.invalid_uris.validator import validate_package
from pprint import pformat
from ckanext.invalid_uris import helpers

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def uri_validation_background_job(type='created', package_types=['dataset', 'dataservice'],
                                  validator='qdes_uri_validator'):
    u"""
    Background job for uri validation.
    """
    # Filter the packages that meet the date criteria.
    packages = []
    query = Session.query(Package).filter(Package.state == 'active')
    start_time = datetime.now() - timedelta(hours=24)
    if type == 'created':
        packages = query.filter(Package.metadata_created >= start_time).all()
    elif type == 'updated':
        packages = query.filter(Package.metadata_modified >= start_time).all()
    elif type == 'all':
        packages = query.all()

    # Load the field that need to be validated.
    uri_fields = get_action('get_schema_uri_fields')(
        {}, {'package_types': package_types, 'validator': validator}
    )

    for package in packages:
        validate_package(package.as_dict(), uri_fields)


def process_invalid_uris(entity_types):
    site_user = get_action(u'get_site_user')({u'ignore_auth': True}, {})
    context = {u'user': site_user[u'name']}
    invalid_uris = get_action('get_invalid_uris')(context, {'entity_types': entity_types})
    contact_points = {}
    for invalid_uri in invalid_uris:
        dataset_dict = get_action('package_show')(context, {'id': invalid_uri.get('parent_entity_id', None) or invalid_uri.get('entity_id', None)})
        contact_point = dataset_dict.get('contact_point', None)
        datasets = contact_points.get(contact_point, [])
        # Only add dataset if it does not already exist in datasets list
        dataset = {'dataset_name': dataset_dict.get('name'), 'dataset_type': dataset_dict.get('type')}
        datasets.append(dataset) if dataset not in datasets else datasets
        contact_points[contact_point] = datasets

    for contact_point_url in contact_points:
        log.debug('contact_point_url: {}'.format(contact_point_url))
        dataset_urls = []
        for dataset in contact_points[contact_point_url]:
            dataset_url = toolkit.url_for('{}.read'.format(dataset.get('dataset_type', None)), id=dataset.get('dataset_name', None), _external=True)
            log.debug('dataset_url {0} for dataset type {1} and name {2}'.format(dataset_url, dataset.get('dataset_type', None), dataset.get('dataset_name', None)))
            if dataset_url:
                dataset_urls.append(dataset_url)

        # Only email contact point if there are dataset URL
        if len(dataset_urls) > 0:
            contact_point_data = helpers.get_contact_point_data(contact_point_url)
            recipient_name = contact_point_data.get('Name', '')
            # TODO: Uncomment line below once story has been implemented https://it-partners.atlassian.net/browse/DDCI-41
            # recipient_email = contact_point_data.get('Email', '')
            recipient_email = 'mark.calvert@salsadigital.com.au'
            subject = toolkit.render('emails/subject/invalid_urls.txt')
            body = toolkit.render('emails/body/invalid_urls.txt', {'recipient_name': recipient_name, 'dataset_urls': dataset_urls})
            toolkit.enqueue_job(toolkit.mail_recipient, [recipient_name, recipient_email, subject, body])
