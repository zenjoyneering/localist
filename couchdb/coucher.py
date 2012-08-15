#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Simple CouchDB cli-based utility.
"""

import json
import httplib
from urlparse import urlsplit
import mimetypes
import os

available_commands = {}


def command(title, usage=""):
    """Decorates any function as application command"""
    global available_commands

    def decorator(f):
        f.ui_title = title
        f.ui_usage = usage
        available_commands[f.__name__] = f
        return f
    return decorator


class attachment(object):
    """Document attachment wrapper"""

    def __init__(self, filename, name=None):
        self.name = name and name or filename
        (doctype, enc) = mimetypes.guess_type(filename)
        self.contentType = doctype and doctype or 'text'
        self.f = filename

    def read(self):
        return open(self.f).read().strip()

    def __repr__(self):
        return "%s: %s" % (self.f, self.contentType)

    def __str__(self):
        return self.read()


class CouchDB(object):
    """Simple API for work with CouchDB using
    hash-map like interface.
    Actually, wrapper around HTTPConnection.
    """

    def __init__(self, dburl, user=None, password=None):
        url = urlsplit(dburl)
        self.name = url.path
        self.headers = {}
        port = url.port and url.port or 80
        self.conn = httplib.HTTPConnection(url.hostname, port)
        self.user = user and user or url.username
        password = password and password or url.password
        if self.user and password:
            self._login(self.user, password)

    def _login(self, name, password):
        self.conn.connect()
        data = "name=%s&password=%s" % (name, password)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.conn.request('POST', "/_session", body=data, headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            self.conn.close()
            return False
        for (k, v) in response.getheaders():
            if k.lower() == 'set-cookie':
                self.headers['Cookie'] = v
        self.conn.close()
        return True

    def __getitem__(self, id):
        return self.get(id)

    def __setitem__(self, id, data):
        self.update(id, data)

    def get(self, docId=None):
        if not docId:
            return self.info()
        self.conn.connect()
        self.conn.request("GET", os.path.join(self.name, docId))
        response = self.conn.getresponse()
        if response.status == 200:
            result = json.loads(response.read())
        else:
            result = None
        self.conn.close()
        return result

    def createdb(self):
        self.conn.connect()
        self.conn.request("PUT", self.name, headers=self.headers)
        response = self.conn.getresponse()
        body = json.loads(response.read())
        self.conn.close()
        if response.status != 200 and response.status != 201:
            raise Exception("%s: %s" % (body['error'], body['reason']))

    def create(self, doc=None, **options):
        if not doc:
            self.createdb()
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        if isinstance(doc, basestring):
            data = doc
        elif isinstance(doc, attachment) and \
                doc.contentType == 'application/json':
            data = doc.read()
        else:
            data = json.dumps(doc)
        self.conn.request('POST', self.name, body=data, headers=headers)
        response = self.conn.getresponse()
        result = json.loads(response.read())
        self.conn.close()
        if response.status == 201:
            return result
        else:
            raise Exception("%s: %s", (result['error'], result['reason']))

    def update(self, id, doc, **options):
        info = self.info(id)
        url = os.path.join(self.name, id)
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        if isinstance(doc, attachment):
            headers['Content-Type'] = doc.contentType
            data = str(doc)
            if doc.contentType != 'application/json' and info:
                # seems to be an attachment
                url = (os.path.join(self.name, id, doc.name) + '?rev=' + \
                        info['rev']).encode('utf-8')
        elif isinstance(doc, basestring):
            # well, if encoded json have _rev field, all be ok.
            data = doc
        else:
            if info:
                doc['_rev'] = info['rev']
            data = json.dumps(doc)
        self.conn.request('PUT', url, body=data, headers=headers)
        response = self.conn.getresponse()
        status = (response.status == 200 or response.status == 201) and True or False
        self.conn.close()
        return status

    def delete(self, doc=None, rev=None):
        if doc is None:
            # deleting an db itself
            self.conn.connect()
            self.conn.request('DELETE', self.name, "", self.headers)
            resp = self.conn.getresponse()
            status = resp.status == 200 and True or False
            self.conn.close()
        else:
            info = self.info(doc)
            if not info:
                raise Exception("Document not found")
            self.conn.connect()
            # @TODO Use urlsplit result here
            url = "%s/%s?rev=%s" % (self.name, doc, info["rev"])
            self.conn.request('DELETE', url, "", self.headers)
            resp = self.conn.getresponse()
            status = resp.status == 200 and True or False
            self.conn.close()
        return status

    def load(self, docs):
        if not docs:
            return None
        url = "%s/_bulk_docs" % self.name
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        data = json.dumps({"docs": docs})
        self.conn.connect()
        self.conn.request('POST', url, body=data, headers=headers)
        response = self.conn.getresponse()
        status = (response.status == 200 or response.status == 201) and True or False
        self.conn.close()
        return status

    def info(self, doc=None):
        info = None
        self.conn.connect()
        if doc:
            # getting info about the doc
            self.conn.request("HEAD", os.path.join(self.name, doc))
            response = self.conn.getresponse()
            if response.status == 200:
                info = {
                    "size": response.getheader('Content-Length'),
                    "rev": response.getheader('ETag')[1:-1]
                }
        else:
            # getting info aboud db itself
            self.conn.request('GET', self.name)
            response = self.conn.getresponse()
            if response.status == 200:
                info = json.loads(response.read())
        self.conn.close()
        return info

    def view(self, viewname, **options):
        viewname = os.path.join(self.name, viewname)
        result = None
        self.conn.connect()
        query = "&".join(["%s=%s" % (k, json.dumps(v)) for (k, v) in options.items()])
        url = query and "%s?%s" % (viewname, query) or viewname
        self.conn.request('GET', url)
        response = self.conn.getresponse()
        result = json.loads(response.read())
        self.conn.close()
        return result


def push_dir(dir, db):
    doc = {}
    attachments = []
    build_doc_from_dir(dir, doc, attachments)
    docId = '_id' in doc and doc['_id'] or dir
    db[docId] = doc
    for (name, f) in attachments:
        m = attachment(f, name)
        db[docId] = m


def attach_files(path, attachments):
    for (dir, dirs, files) in os.walk(path, followlinks=True):
        for d in dirs:
            if d.startswith('.'):
                dirs.remove(d)
        if files:
            p = os.path.relpath(dir, path)
            for f in [fname for fname in files if not fname.startswith('.')]:
                name = p == "." and f or os.path.join(p, f)
                attachments.append((name, os.path.join(dir, f)))


def build_doc_from_dir(path, doc, attachments):
    for name in os.listdir(path):
        if name.startswith('.'):
            continue
        if name == '_attachments':
            attach_files(os.path.join(path, name), attachments)
        elif os.path.isdir(os.path.join(path, name)):
            doc[name] = {}
            build_doc_from_dir(os.path.join(path, name), doc[name], attachments)
        else:
            m = attachment(os.path.join(path, name))
            (n, ext) = os.path.splitext(name)
            key = (ext == '.js' or ext == '.json') and n or name
            if n == 'manifest':
                manifest = json.loads(str(m))
                doc.update(manifest)
            else:
                try:
                    doc[key] = json.loads(str(m))
                except Exception:
                    doc[key] = str(m)


@command("Create new CouchDB database")
def createdb(url):
    db = CouchDB(url)
    db.createdb()


@command("Delete a database")
def dropdb(url):
    db = CouchDB(url)
    db.delete()


@command("Push document, created from directory contents to DB")
def push(source, url):
    if not os.path.exists(source):
        return
    db = CouchDB(url)
    doc = {}
    attachments = []
    build_doc_from_dir(source, doc, attachments)
    docId = '_id' in doc and doc['_id'] or dir
    db[docId] = doc
    for (name, f) in attachments:
        m = attachment(f, name)
        db[docId] = m


def main():
    global available_commands
    import sys
    if len(sys.argv) < 2:
        print("Usage: {0} command".format(sys.argv[0]))
        sys.exit(1)
    cmd_name = sys.argv[1]
    if not cmd_name in available_commands:
        print("Command {0} not supported".format(cmd_name))
        sys.exit(1)
    cmd = available_commands.get(cmd_name)
    cmd(*sys.argv[2:])


if __name__ == "__main__":
    main()
