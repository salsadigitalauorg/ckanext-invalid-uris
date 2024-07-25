import ckan.plugins.toolkit as toolkit
import click
import ckanext.invalid_uris.jobs as jobs

from ckanext.invalid_uris import helpers


@click.command(u"register-uri-validation-job")
@click.option(u"-t", u"--type", required=True,
              help=u"""Type of the job.
              
                Possible values:  
                
                'created' => filter package by created date within last 24h
                
                'updated' => filter package by updated/modified date within last 24h
                
                'all' => get all metadata
              """)
@click.option(u"-p", u"--package_types", required=True,
              help=u"List of the package types, separated by a space, eg 'dataset dataservice'")
@click.option(u"-v", u"--validator", required=True,
              help=u"The name of the uri validator, eg. 'qdes_uri_validator' or 'datant_uri_validator'")
def register_uri_validation_job(type, package_types, validator):
    u"""
    Enqueue the url validation to the background job.
    """
    # Improvements for job worker visibility when troubleshooting via logs
    job_title = f'Adding URI validation job to background queue: type={type}, package_types={package_types}, validator={validator}'
    toolkit.enqueue_job(jobs.uri_validation_background_job, [type, package_types.split(), validator], title=job_title, rq_kwargs={'timeout': 3600})


@click.command(u"process-invalid-uris")
@click.option(u"-e", u"--entity_types", required=True,
              help=u"List of the entity types, separated by a space, eg: 'dataset dataservice resource' or 'dataset resource")
@click.pass_context
def process_invalid_uris(ctx, entity_types):
    u"""
    Process invalid URI's and email point of contact with a list of datasets with invalid URI's in the metadata
    """
    click.secho(u"Begin processing invalid URI's for entity types {}".format(entity_types.split()), fg=u"green")

    try:
        flask_app = ctx.meta['flask_app']
        with flask_app.test_request_context():
            jobs.process_invalid_uris(entity_types.split())
    except Exception as e:
        click.secho(f"Failed processing invalid URI's: {e}", fg=u"red")

    click.secho(u"Finished processing invalid URI's", fg=u"green")


@click.command(u"validate-packages")
@click.option(u"-i", u"--package_ids", required=True, 
              help=u"Comma separated list of package_ids or invalid_uris to validate all current invalid_uri packages")
@click.option(u"-p", u"--package_types", required=True,
              help=u"List of the package types, separated by a space, eg 'dataset dataservice'")
@click.option(u"-v", u"--validator", required=True,
              help=u"The name of the uri validator, eg. 'qdes_uri_validator' or 'datant_uri_validator'")
def validate_packages(package_ids, package_types, validator):
    u"""
    Validate a package
    """
    jobs.validate_packages_job(package_ids, package_types, validator)


@click.command(u"validate-uri")
@click.option('-u', '--uri', required=True, 
              help='Check if the given uri is valid or not')
def validate_uri(uri):
    click.echo(f'Validating URI {uri}')
    response = helpers.valid_uri(uri)
    if response.get('valid'):
        click.secho(f'Response success: {str(response)}', fg='green')
    else:
        click.secho(f'Response failed: {str(response)}', fg='red')


def get_commands():
    return [register_uri_validation_job, process_invalid_uris, validate_packages, validate_uri]
