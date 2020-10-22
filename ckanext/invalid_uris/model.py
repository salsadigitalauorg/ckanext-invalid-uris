import datetime

from ckan.model import meta
from ckan.model import types as _types
from sqlalchemy import types, Column, Table, func, ForeignKey
from ckan.model.domain_object import DomainObject

# Define invalid_uri table structure.
invalid_uri_table = Table(
    'invalid_uri', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('entity_type', types.UnicodeText, nullable=False),
    Column('entity_id', types.UnicodeText, nullable=False),
    Column('parent_entity_id', types.UnicodeText),
    Column('field', types.UnicodeText, nullable=False),
    Column('uri', types.UnicodeText, nullable=False),
    Column('status_code', types.UnicodeText, nullable=False),
    Column('reason', types.UnicodeText, nullable=False),
    Column('date_created', types.DateTime, default=datetime.datetime.utcnow()),
    Column('date_last_checked', types.DateTime, default=datetime.datetime.utcnow()),
)


class InvalidUri(DomainObject):
    u"""
    An InvalidUri object.
    """

    def __init__(self, entity_type=None, entity_id=None, parent_entity_id=None, field=None, uri=None,
                 status_code=None, reason=None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.parent_entity_id = parent_entity_id
        self.field = field
        self.uri = uri
        self.status_code = status_code
        self.reason = reason

    @classmethod
    def is_uri_exist(cls, uri):
        """
        Returns true if there is a matching uri.
        """
        query = meta.Session.query(cls)
        return query.filter(func.lower(cls.uri) == func.lower(uri)).first() is not None

    @classmethod
    def filter(cls, data):
        """
        Returns if there is a matching uri/field name/entity type/entity id/parent entity id.
        """
        query = meta.Session.query(cls)

        if data.get('uri'):
            query = query.filter(func.lower(cls.uri) == func.lower(data.get('uri')))

        if data.get('field'):
            query = query.filter(cls.field == data.get('field'))

        if data.get('entity_type'):
            query = query.filter(cls.entity_type == data.get('entity_type'))

        if data.get('entity_id'):
            query = query.filter(cls.entity_id == data.get('entity_id'))

        if data.get('parent_entity_id'):
            query = query.filter(cls.parent_entity_id == data.get('parent_entity_id'))

        return query.all()

    @classmethod
    def get_by_uri(cls, uri):
        """
        Returns if there is a matching uri.
        """
        query = meta.Session.query(cls)
        return query.filter(func.lower(cls.uri) == func.lower(uri)).all()


meta.mapper(InvalidUri, invalid_uri_table)
