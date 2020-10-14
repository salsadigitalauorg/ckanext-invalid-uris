import ckan.plugins.toolkit as toolkit
import click
import logging

from datetime import datetime
from ckanapi import LocalCKAN, ValidationError
from ckanext.invalid_uris import model
from ckanext.invalid_uris.jobs import uri_validation_background_job
from pprint import pformat

log = logging.getLogger(__name__)


@click.command(u"register-uri-validation-job")
@click.option(u"-t", u"--type", default=u"created", help=u"Type of the job, 'created', 'updated' or 'all'")
@click.option(u"-p", u"--package_types", default=u"dataset dataservice",
              help=u"List of the package types, comma separated, example 'dataset dataservice'")
@click.option(u"-v", u"--validator", default=u"qdes_uri_validator", help=u"The name of the uri validator")
def register_uri_validation_job(type='created', package_types='dataset dataservice', validator='qdes_uri_validator'):
    log.debug('Adding job to background queue:')
    log.debug('type %s' % pformat(type))
    log.debug('package_types %s' % pformat(package_types.split()))
    log.debug('validator %s' % pformat(validator))
    toolkit.enqueue_job(uri_validation_background_job, [type, package_types.split(), validator])


@click.command(u"invalid-uris-init-db")
def init_db_cmd():
    """Initialise the database tables required for internal vocabulary services
    """
    click.secho(u"Initializing invalid_uri table", fg=u"green")

    try:
        model.invalid_uri_table.create()
    except Exception as e:
        log.error(str(e))

    click.secho(u"Table invalid_uri is setup", fg=u"green")


def get_commands():
    return [init_db_cmd, register_uri_validation_job]
