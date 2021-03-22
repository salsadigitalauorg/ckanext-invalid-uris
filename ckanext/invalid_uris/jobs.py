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
        try:
            context.pop('__auth_audit', None)
            dataset_dict = get_action('package_show')(context, {'id': invalid_uri.get('parent_entity_id', None) or invalid_uri.get('entity_id', None)})

            if dataset_dict.get('state') == 'active':
                contact_point = dataset_dict.get('contact_point', None)
                datasets = contact_points.get(contact_point, [])
                # Only add dataset if it does not already exist in datasets list
                title = dataset_dict.get('title')
                name = dataset_dict.get('name')
                url = toolkit.url_for('{}.read'.format(dataset_dict.get('type', None)), id=name, _external=True)
                dataset = {'title': title, 'url': url}
                datasets.append(dataset) if dataset not in datasets else datasets
                contact_points[contact_point] = datasets
        except Exception as e:
            log.error(str(e))

    for contact_point in contact_points:
        datasets = contact_points[contact_point]
        # Only email contact point if there are datasets
        if len(datasets) > 0:
            contact_point_data = get_action('get_secure_vocabulary_record')(context, {'vocabulary_name': 'point-of-contact', 'query': contact_point})
            if contact_point_data:
                recipient_name = contact_point_data.get('Name', '')
                recipient_email = contact_point_data.get('Email', '')
                subject = toolkit.render('emails/subject/invalid_urls.txt')
                body = toolkit.render('emails/body/invalid_urls.txt', {'recipient_name': recipient_name, 'datasets': datasets})
                body_html = toolkit.render('emails/body/invalid_urls.html', {'recipient_name': recipient_name, 'datasets': datasets})

                # Remove CRLF from email.
                recipient_email = recipient_email.replace('\r\n', '').replace('\r', '').replace('\n', '').replace('^M', '')

                # Improvements for job worker visibility when troubleshooting via logs
                job_title = 'Invalid URI email notification to {}'.format(recipient_email)
                log.debug('Enqueuing job: "{}"'.format(job_title))

                job = toolkit.enqueue_job(
                    toolkit.mail_recipient,
                    [recipient_name, recipient_email, subject, body, body_html],
                    title=job_title
                )

                log.debug('Job enqueued: "{0}" (ID: {1})'.format(job_title, job.id))
