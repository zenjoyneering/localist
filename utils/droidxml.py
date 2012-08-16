#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import glob
from urlparse import urlsplit
from urllib import urlencode
from lxml import etree
import json
import httplib


class DroidXML(object):
    """Simple and basic android resource bundle interface"""
    STRINGS = "strings*.xml"    # localizeable files pattern
    TRANSLATED = "values-*"     # translated resources patterns
    SOURCE = "values"           # source strings

    AVAIL_COMMANDS = ["pull", "push"]

    def __init__(self, resource_dir="res"):
        self.basepath = resource_dir

    def create_msg(self, domain, key, locale, source=None):
        """Create message JSON-serializeable representation"""
        i18n = {
            "key": key,
            "domain": domain,
            "locale": locale,
        }
        if source:
            i18n['source'] = source
        return i18n

    def already_uploaded(self, url, lang="en"):
        """Download already uploaded strings and return keymap"""
        db_url = urlsplit(url)
        http = httplib.HTTPConnection(db_url.hostname, db_url.port or 80)
        options = urlencode({
            "reduce": "false",
            "startkey": '["en"]',
            "endkey": '["en", {}]'
        })
        view = os.path.join(
            db_url.path,
            "_design/i18n/_view/translations?%s" % options
        )
        http.request("GET", view)
        response = http.getresponse()
        data = json.loads(response.read())
        http.close()
        keymap = {}
        for row in data['rows']:
            key = "{form}:{domain}:{key}".format(
                form='message' in row['value']['i18n'] and 'str' or 'pl',
                domain=row['value']['i18n']['domain'],
                key=row['value']['i18n']['key']
            )
            keymap[key] = row['value']
        return keymap

    def resources(self, values, lang="en_US", source_strings={}):
        """Extract resources from given dir for given language code"""
        search = os.path.join(values, self.STRINGS)
        files = glob.glob(search)
        for source in files:
            (path, fname) = os.path.split(source)
            (domain, ext) = os.path.splitext(fname)
            xml = etree.parse(source)
            for node in xml.getroot():
                if node.tag == 'string':
                    original = source_strings.get('str:%s' % node.attrib['name'])
                    i18n = self.create_msg(domain, node.attrib['name'], lang, original)
                    i18n['message'] = node.text or ""
                    yield i18n
                elif node.tag == 'plurals':
                    original = source_strings.get('pl:%s' % node.attrib['name'])
                    i18n = self.create_msg(domain, node.attrib['name'], lang, original)
                    plurals = {}
                    for item in node.iterfind('item'):
                        plurals[item.attrib['quantity']] = item.text
                    i18n['plurals'] = plurals
                    yield i18n

    def translations(self, values_dir, lang, source_strings, domain_lookup):
        """Extract translations and set correct domain, even if translation
           directory contains all translated resources as single strings.xml
        """
        for i18n in self.resources(values_dir, lang, source_strings):
            i18n['domain'] = domain_lookup.get(i18n['key']) or i18n['domain']
            yield i18n

    def translated(self):
        """Return all tranlslated resource dirs
           Return list of (locale, dir) tuples
        """
        search = os.path.join(self.basepath, self.TRANSLATED)
        dirs = glob.glob(search)
        res = []
        for d in dirs:
            #strip trailing slash
            d = d[-1] == '/' and d[:-1] or d
            (path, source) = os.path.split(d)
            (_base, locale) = source.split("-", 1)
            res.append((locale, d))
        return res

    def map_meta(self, doc, meta):
        """Maps each inserted doc's id and rev from meta to doc by key"""
        if 'message' in doc['i18n']:
            return ("str:%s" % doc['i18n']['key'], meta)
        elif 'plurals' in doc['i18n']:
            return ("pl:%s" % doc['i18n']['key'], meta)

    def push(self, url):
        """Push all resources (including translated) to db"""
        db_url = urlsplit(url)
        http = httplib.HTTPConnection(db_url.hostname, db_url.port or 80)
        bulk_docs_url = os.path.join(db_url.path, "_bulk_docs")
        headers = {"Content-Type": "application/json"}

        values = os.path.join(self.basepath, self.SOURCE)
        docs = map(lambda i18n: {"i18n": i18n}, self.resources(values, "en"))

        uploaded = self.already_uploaded(url, "en")
        if uploaded:
            docs_for_update = []
            for doc in docs:
                i18n = doc['i18n']
                key = "{form}:{domain}:{key}".format(
                    form='message' in i18n and 'str' or 'pl',
                    domain=i18n['domain'],
                    key=i18n['key']
                )
                if not key in uploaded:
                    # this is a fresh key
                    docs_for_update.append({"i18n": i18n})
                elif 'message' in i18n and i18n['message'] != uploaded[key]['i18n']['message']:
                    # update a message
                    doc = uploaded[key]
                    doc['i18n']['message'] = i18n['message']
                    docs_for_update.append(doc)
                elif 'plurals' in i18n:
                    # plural, and key already exists
                    stored = uploaded[key]['i18n']['plurals'].values()
                    stored.sort()
                    fresh = i18n['plurals'].values()
                    fresh.sort()
                    if stored != fresh:
                        doc = uploaded[key]
                        doc['i18n']['plurals'] = i18n['plurals']
                        docs_for_update.append(doc)
            bulk = json.dumps({"docs": docs_for_update})
            http.request("POST", bulk_docs_url, body=bulk, headers=headers)
            response = http.getresponse()
            meta_data = json.loads(response.read())
            print("{0} msgs loaded".format(len(meta_data)))
            http.close()
        else:
            bulk = json.dumps({"docs": docs})
            http.request("POST", bulk_docs_url, body=bulk, headers=headers)
            response = http.getresponse()
            meta_data = json.loads(response.read())
            print("{0} msgs loaded".format(len(meta_data)))
            http.close()

            # map each strings key do a doc's id and rev
            sources = dict(map(self.map_meta, docs, meta_data))

            map_domain = lambda doc: (doc['i18n']['key'], doc['i18n']['domain'])
            domain_lookup = dict(map(map_domain, docs))

            for (locale, values_dir) in self.translated():
                docs = map(
                    lambda i18n: {"i18n": i18n},
                    self.translations(values_dir, locale, sources, domain_lookup)
                )
                bulk = json.dumps({"docs": docs})
                http.request("POST", bulk_docs_url, body=bulk, headers=headers)
                response = http.getresponse()
                meta_data = json.loads(response.read())
                http.close()
                print("{0} {1} translations loaded".format(len(meta_data), locale))

    def pull(self, url):
        """Pull all translations from db and store it"""
        # get all available domains from db,
        db_url = urlsplit(url)
        http = httplib.HTTPConnection(db_url.hostname, db_url.port or 80)
        view = os.path.join(
            db_url.path,
            "_design/i18n/_view/translations?group_level=2"
        )
        http.request("GET", view)
        response = http.getresponse()
        data = json.loads(response.read())
        #http.close()
        domains = {}
        for doc in data['rows']:
            (locale, domain) = doc['key']
            if not locale in domains:
                domains[locale] = []
            domains[locale].append(domain)
        for (locale, values_dir) in self.translated():
            for domain in domains[locale]:
                options = urlencode({
                    'reduce': 'false',
                    'key': '["%s", "%s"]' % (locale, domain)
                })
                xml_url = os.path.join(
                    db_url.path,
                    "_design/i18n/_list/android-xml/translations"
                )
                http.request("GET", "%s?%s" % (xml_url, options))
                resp = http.getresponse()
                xml = resp.read()
                # writing translations
                xml_filename = os.path.join(values_dir, domain) + ".xml"
                print("Writing {0}".format(xml_filename))
                xml_file = open(os.path.join(values_dir, domain) + ".xml", "w")
                xml_file.write(xml)
                xml_file.close()
        # recreate all (except source)
        http.close()


def main():
    import sys
    if (len(sys.argv) < 3):
        print("Usage: {0} <push|pull> <db_url> [options....]".format(*sys.argv))
        sys.exit(1)

    cmd = sys.argv[1]
    if not cmd in DroidXML.AVAIL_COMMANDS:
        print("Command '{0}' not supported".format(cmd))
        print("Available commands: {0}".format(", ".join(DroidXML.AVAIL_COMMANDS)))
        sys.exit(1)

    url = sys.argv[2]
    res_dir = len(sys.argv) == 4 and sys.argv[3] or "res"
    if not os.path.exists(res_dir):
        print("Resource dir not found")
        sys.exit(1)

    resource = DroidXML(res_dir)
    cmd = getattr(resource, cmd)
    cmd(url)

if __name__ == "__main__":
    main()
