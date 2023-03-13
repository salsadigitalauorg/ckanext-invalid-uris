from ckan.plugins.interfaces import Interface


class IInvalidURIs(Interface):
    u'''
    This interface allows plugins to hook into the Invalid URIs
    '''

    def contact_point_data(self, context, contact_point):
        """
        :returns: a dictionary of contact point data including name and email
        :rtype: dictionary
        """
