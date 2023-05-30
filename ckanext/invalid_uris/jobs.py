import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from datetime import datetime, timedelta
from ckan.model import Session
from ckan.model.package import Package
from ckanext.invalid_uris.validator import validate_package
from ckanext.invalid_uris.model import InvalidUri
from ckanext.invalid_uris.interfaces import IInvalidURIs
from ckan.model.core import State

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def uri_validation_background_job(type, package_types, validator):
    u"""
    Background job for uri validation.
    """
    # Filter the packages that meet the date criteria.
    packages = []
    query = Session.query(Package).filter(Package.state == State.ACTIVE)
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
        validate_package(package_as_dict(package), uri_fields)


def process_invalid_uris(entity_types):
    site_user = get_action(u'get_site_user')({u'ignore_auth': True}, {})
    context = {u'user': site_user[u'name']}
    invalid_uris = get_action('get_invalid_uris')(context, {'entity_types': entity_types})
    contact_points = {}

    for invalid_uri in invalid_uris:
        try:
            context.pop('__auth_audit', None)
            dataset_dict = {}
            resource_dict = {}
            dataset = None
            if invalid_uri.get('entity_type') == 'dataset':
                dataset_dict = get_action('package_show')(context, {'id': invalid_uri.get('entity_id')})
                if dataset_dict.get('state') == State.ACTIVE:
                    title = dataset_dict.get('title')
                    package_name = dataset_dict.get('name')
                    package_type = dataset_dict.get('type')
                    url = toolkit.url_for('{}.read'.format(package_type), id=package_name, _external=True)
                    dataset = {'title': title, 'url': url}
            elif invalid_uri.get('entity_type') == 'resource':
                resource_dict = get_action('resource_show')(context, {'id': invalid_uri.get('entity_id')})
                title = resource_dict.get('name')
                resource_id = resource_dict.get('id')
                dataset_dict = get_action('package_show')(context, {'id': invalid_uri.get('parent_entity_id')})
                if dataset_dict.get('state') == State.ACTIVE and resource_dict.get('state') == State.ACTIVE:
                    package_name = dataset_dict.get('name')
                    package_type = dataset_dict.get('type')
                    url = toolkit.url_for('dataset_resource.read', id=package_name, resource_id=resource_id, package_type=package_type, _external=True)
                    dataset = {'title': title, 'url': url}

            if dataset:
                contact_point = dataset_dict.get('contact_point', 1)
                datasets = contact_points.get(contact_point, [])
                # Only add dataset if it does not already exist in datasets list
                datasets.append(dataset) if dataset not in datasets else datasets
                contact_points[contact_point] = datasets
            else:
                # Remove it from invalid_uri table.
                get_action('delete_invalid_uri')(context, invalid_uri)
        except toolkit.ObjectNotFound:
            # Remove it from invalid_uri table.
            get_action('delete_invalid_uri')(context, invalid_uri)
        except Exception as e:
            log.error(str(e))

    for contact_point in contact_points:
        datasets = contact_points[contact_point]
        # Only email contact point if there are datasets
        if len(datasets) > 0:
            recipient_name = toolkit.config.get('ckanext.invalid_uris.recipient_name')
            recipient_email = toolkit.config.get('ckanext.invalid_uris.recipient_email')
            for plugin in plugins.PluginImplementations(IInvalidURIs):
                contact_point_data = plugin.contact_point_data(context, contact_point)
                if contact_point_data:
                    recipient_name = contact_point_data.get('Name') or contact_point_data.get('name')
                    recipient_email = contact_point_data.get('Email') or contact_point_data.get('email')

            if not recipient_name and not recipient_email:
                log.error(f'Recipient name and email is not set. recipient_name:{recipient_name} recipient_email:{recipient_email}')
                continue

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


def validate_packages_job(package_ids, package_types, validator):
    uri_fields = get_action('get_schema_uri_fields')(
        {}, {'package_types': package_types, 'validator': validator}
    )

    if package_ids == 'invalid_uris':
        invalid_uris = Session.query(InvalidUri).all()
        package_ids = [invalid_uri.parent_entity_id if invalid_uri.entity_type == 'resource' else invalid_uri.entity_id for invalid_uri in invalid_uris]
    else:
        package_ids = package_ids.split(',')

    for package_id in package_ids:
        package = Session.query(Package).filter(Package.id == package_id).first()
        validate_package(package_as_dict(package), uri_fields)


def package_as_dict(package):
    pkg_dict = package.as_dict()
    resources = []
    for resource in package.resources_all:
        res_dict = resource.as_dict(core_columns_only=False)
        # resource.as_dict does not return the resource state metadata field
        # manually set the state field
        res_dict['state'] = resource.state
        resources.append(res_dict)
    pkg_dict['resources'] = resources
    return pkg_dict
