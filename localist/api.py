#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from httplib import HTTPConnection
from urlparse import urlsplit
from urllib import urlencode
import os.path
from localist import Resource


class Service(object):
    """Localist web-service API"""

    RESOURCES_URI = "_design/i18n/_view/resources"

    def __init__(self, url, username=None, password=None):
        self.url = urlsplit(url)
        self.username = username or self.url.username
        self.password = password or self.url.password
        self._auth_token = None
        self.conn = HTTPConnection(self.url.hostname, self.url.port or 80)

    def login(self):
        """Login to couchdb using cookie-based authentication"""
        if self._auth_token:
            return True
        self.conn.connect()
        data = urlencode({
            "name": self.username,
            "password": self.password
        })
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.conn.request('POST', "/_session", body=data, headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            self.conn.close()
            return False
        for (key, val) in response.getheaders():
            if key.lower() == 'set-cookie':
                self._auth_token = val
        self.conn.close()
        return True

    def resources(self, project, locale):
        """Get all resource for project in given locale"""
        self.login()
        self.conn.connect()
        options = urlencode({
            "reduce": "false",
            "startkey": '["{}", "{}"]'.format(project, locale),
            "endkey": '["{}", "{}", {{}}]'.format(project, locale)
        })
        view = os.path.join(
            self.url.path,
            "{url}?{options}".format(url=self.RESOURCES_URI, options=options)
        )
        self.conn.request("GET", view, headers={'Cookies': self._auth_token})
        response = json.loads(self.conn.getresponse().read())
        self.conn.close()
        return (Resource(**doc['value']) for doc in response['rows'])

    def update(self, project, resources):
        """Make a bulk_docs-ready format, push a bulk.
           returns an id and rev of updated docs"""
        self.login()
        docs = []
        # TODO: Attach created/updated fields
        for resource in resources:
            resource.project = project
            docs.append(resource.as_dict)
        if not docs:
            return []
        bulk = {
            'docs': docs
        }
        bulk_docs_url = os.path.join(self.url.path, "_bulk_docs")
        headers = {
            'Content-Type': "application/json",
            'Cookies': self._auth_token
        }
        self.conn.request(
            'POST', bulk_docs_url,
            body=json.dumps(bulk), headers=headers
        )
        resp = json.loads(self.conn.getresponse().read())
        return resp
