import click
import logging

from ckanapi import LocalCKAN, ValidationError
from ckanext.invalid_uris import model
from datetime import datetime

log = logging.getLogger(__name__)

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
    return [init_db_cmd]
