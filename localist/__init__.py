#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a simple client for localist web-service.

Can be used as a command line tool and as a library.
See docs for more information.
"""

import json


class Resource(object):
    """Base localizable resource"""

    def __init__(self, **kwargs):
        """
        Constructor, arguments is:

        ``locale``
            Resource's locale code

        ``message``
            Localizable text

        ``plurals``
            Pluarls form

        ``name``
            Resource name

        ``domain``
            Resource domain (filename)
        """
        # some implementation notes:
        # Guaranteed intitalization of required fields
        _data = {
            'type': "i18n.resource",
            'project': kwargs.get('project'),
            'locale': kwargs.get('locale', ""),
            'domain': kwargs.get('domain', ""),
            'name': kwargs.get('name', "")
        }
        # determine type of resource
        if 'plurals' in kwargs:
            _data['plurals'] = kwargs.get('plurals')
        else:
            _data['message'] = kwargs.get('message', "")
        # All extra fileds are stored too (for the user-defined fields (source,
        # eg.
        _data.update(kwargs)
        # separate _data property that actual store all data allows us
        # to transparently save all extra user-defined fields
        self.__dict__['_data'] = _data

    @property
    def is_plural(self):
        """Checks if the resource is plurals"""
        return bool(self._data.get('plurals'))

    @property
    def text(self):
        """Returns the text key of the resource"""
        if self.is_plural:
            return self._data['plurals'].get('other', "")
        else:
            return self.message

    @property
    def as_json(self):
        """Convert resource to json representation"""
        return json.dumps(self._data)

    @property
    def as_dict(self):
        """Return internal state"""
        return self._data

    # Black magic start here:
    def __eq__(self, other):
        return type(self) == type(other) and self.text == other.text

    def __getattr__(self, name):
        return self._data.get(name)

    def __setattr__(self, name, val):
        self._data[name] = val


class Backend(object):
    """Base interface for backend to be implemented"""

    def locales(self):
        raise Exception("Not implemented")

    def domains(self, locale=None):
        raise Exception("Not implemented")

    def resources(self, locale=None):
        raise Exception("Not implemented")

    def update(self, resources, locale, domain):
        raise Exception("Not implemented")
