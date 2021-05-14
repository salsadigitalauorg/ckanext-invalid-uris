import ckan.plugins.toolkit as toolkit
import click
import logging
import ckanext.invalid_uris.jobs as jobs

from datetime import datetime
from ckanapi import LocalCKAN, ValidationError
from ckanext.invalid_uris import model
from pprint import pformat

log = logging.getLogger(__name__)


@click.command(u"register-uri-validation-job")
@click.option(u"-t", u"--type", default=u"created",
              help=u"""Optional. Type of the job, default: 'created'.
              
                Possible values:  
                
                'created' => filter package by created date within last 24h
                
                'updated' => filter package by updated/modified date within last 24h
                
                'all' => get all metadata
              """)
@click.option(u"-p", u"--package_types", default=u"dataset dataservice",
              help=u"Optional. List of the package types, comma separated, default: 'dataset dataservice'")
@click.option(u"-v", u"--validator", default=u"qdes_uri_validator",
              help=u"Optional. The name of the uri validator, default: 'qdes_uri_validator'")
def register_uri_validation_job(type='created', package_types='dataset dataservice', validator='qdes_uri_validator'):
    u"""
    Enqueue the url validation to the background job.
    """
    log.debug('Adding URI validation job to background queue:')
    log.debug('type %s' % pformat(type))
    log.debug('package_types %s' % pformat(package_types.split()))
    log.debug('validator %s' % pformat(validator))
    # Improvements for job worker visibility when troubleshooting via logs
    job_title = f'Adding URI validation job to background queue: type={type}, package_types={package_types}, validator={validator}'
    toolkit.enqueue_job(jobs.uri_validation_background_job, [type, package_types.split(), validator], title=job_title)


@click.command(u"invalid-uris-init-db")
def init_db_cmd():
    u"""
    Initialise the database tables required for internal vocabulary services
    """
    click.secho(u"Initializing invalid_uri table", fg=u"green")

    try:
        model.invalid_uri_table.create()
    except Exception as e:
        log.error(str(e))

    click.secho(u"Table invalid_uri is setup", fg=u"green")


@click.command(u"process-invalid-uris")
@click.option(u"-e", u"--entity_types", default=u"dataset dataservice resource",
              help=u"Optional. List of the entity types, separated by a space, default: 'dataset dataservice resource'")
@click.pass_context
def process_invalid_uris(ctx, entity_types='dataset dataservice resource'):
    u"""
    Process invalid URI's and email point of contact with a list of datasets with invalid URI's in the metadata
    """
    click.secho(u"Begin processing invalid URI's for entity types {}".format(entity_types.split()), fg=u"green")

    try:
        flask_app = ctx.meta['flask_app']
        with flask_app.test_request_context():
            jobs.process_invalid_uris(entity_types.split())
    except Exception as e:
        log.error(e)

    click.secho(u"Finished processing invalid URI's", fg=u"green")


def get_commands():
    return [init_db_cmd, register_uri_validation_job, process_invalid_uris]
