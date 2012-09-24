#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from httplib import HTTPConnection
from urlparse import urlsplit
from urllib import urlencode
import os.path
from localist import Resource
from time import time


class Service(object):
    """Localist web-service API"""

    RESOURCES_URI = "_design/i18n/_view/resources"

    def __init__(self, url, username=None, password=None, proxy=None):
        self.url = urlsplit(url)
        self.base_url = "http://{host}{port}{path}".format(
            host=self.url.hostname,
            port=self.url.port and ":" + str(self.url.port) or "",
            path=self.url.path
        )
        self.username = username or self.url.username
        self.password = password or self.url.password
        self._auth_token = None
        (host, port) = proxy or (self.url.hostname, self.url.port)
        port = port and int(port) or 80
        self.conn = HTTPConnection(host, port)

    def login(self):
        """Login to couchdb using cookie-based authentication"""
        if self._auth_token:
            return True
        if self.username is None or self.password is None:
            return True
        self.conn.connect()
        data = urlencode({
            "name": self.username,
            "password": self.password
        })
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = os.path.join(self.base_url, "_session")
        self.conn.request('POST', url, body=data, headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            self.conn.close()
            return False
        for (key, val) in response.getheaders():
            if key.lower() == 'set-cookie':
                self._auth_token = val
        self.conn.close()
        return True

    def project_info(self, project):
        """Retrieve project info from service"""
        self.login()
        self.conn.connect()
        url = os.path.join(self.base_url, project)
        self.conn.request('GET', url, headers={'Cookie': self._auth_token})
        response = self.conn.getresponse()
        info = response.status == 200 and json.loads(response.read()) or None
        self.conn.close()
        return info

    def register_project(self, project, language, translations, title=None):
        """Register project on service"""
        self.login()
        info = {
            "type": "i18n.project",
            "_id": project,
            "title": title or project,
            "language": language,
            "translations": translations,
            "created": {
                "at": int(time())
            }
        }
        if self.username:
            info['created']['by'] = self.username
        data = json.dumps(info)
        headers = {
            'Cookie': self._auth_token,
            'Content-Type': 'application/json'
        }
        self.conn.connect()
        self.conn.request('POST', self.base_url, body=data, headers=headers)
        response = self.conn.getresponse()
        status = response.status == 201 and True or False
        self.conn.close()
        return status

    def resources(self, project, locale):
        """Get all resource for project in given locale"""
        self.login()
        options = urlencode({
            "reduce": "false",
            "startkey": '["{0}", "{1}"]'.format(project, locale),
            "endkey": '["{0}", "{1}", {{}}]'.format(project, locale)
        })
        view = os.path.join(
            self.base_url,
            "{url}?{options}".format(url=self.RESOURCES_URI, options=options)
        )
        self.conn.connect()
        self.conn.request("GET", view, headers={'Cookie': self._auth_token})
        response = json.loads(self.conn.getresponse().read())
        self.conn.close()
        return (Resource(**doc['value']) for doc in response['rows'])

    def update(self, project, resources):
        """Make a bulk_docs-ready format, push a bulk.
           returns an id and rev of updated docs"""
        self.login()
        docs = []
        # TODO: Attach created/updated fields
        stamp = int(time())
        for resource in resources:
            resource.project = project
            doc = resource.as_dict
            doc['created'] = {
                "at": stamp
            }
            if self.username:
                doc['created']['by'] = self.username
            docs.append(doc)
        if not docs:
            return []
        bulk = {
            'docs': docs
        }
        bulk_docs_url = os.path.join(self.base_url, "_bulk_docs")
        headers = {
            'Content-Type': "application/json",
            'Cookie': self._auth_token
        }
        self.conn.request(
            'POST', bulk_docs_url,
            body=json.dumps(bulk), headers=headers
        )
        resp = json.loads(self.conn.getresponse().read())
        return resp
