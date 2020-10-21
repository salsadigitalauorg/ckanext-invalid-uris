import logging
import ckan.plugins.toolkit as toolkit
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize

from datetime import datetime, timedelta
from ckan.model import Session
from ckan.model.package import Package
from ckanext.invalid_uris.validator import validate_package
from pprint import pformat

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

    context = {'model': model}
    for package in packages:
        validate_package(model_dictize.package_dictize(package, context), uri_fields)
