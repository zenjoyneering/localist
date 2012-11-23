#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML-based i18n backend for android projects
"""

import os.path
import glob
from localist import Resource
from lxml import etree
from xml.sax.saxutils import escape


APOS = {"'": "\\'"}

XML_START = """<?xml version="1.0" encoding="utf-8"?>
<resources>
"""

XML_END = """</resources>"""

XML_STRING = u"""    <string name="{resource.name}">{resource.text}</string>\n"""

XML_PLURALS_START = u"""    <plurals name="{resource.name}">\n"""

XML_PLURALS_ITEM = u"""        <item quantity="{quantity}">{text}</item>\n"""

XML_PLURALS_END = """    </plurals>\n"""


def plurals_to_dict(node):
    """Extract plurals as dict from <plurals> xml node"""
    return dict([
        (it.attrib['quantity'], unicode(it.text))
        for it in node.iterfind('item')
    ])


class AndroidXML(object):
    """Simple and basic android resource bundle interface"""
    STRINGS = "strings*.xml"    # localizeable files pattern
    TRANSLATED = "values-*"     # translated resources patterns
    SOURCE = "values"           # source strings
    SOURCE_LOCALE = "en"        # source (default) locale
    FILEEXT = ".xml"            # extension, that we cut from domain name

    def __init__(self, resource_dir="res", pattern=None):
        self.basepath = resource_dir
        self.search = pattern or self.STRINGS

    def locales(self):
        """Return list of available locales, found in res-folder, w/o source"""
        search = os.path.join(self.basepath, self.TRANSLATED)
        for dirname in glob.glob(search):
            (_, values_dir) = os.path.split(dirname)
            (_, locale) = values_dir.split("-", 1)
            yield locale
        # at last we should yield source locale too
        yield self.SOURCE_LOCALE

    def domain_name(self, domain):
        """Split out *system* extensions from domain name"""
        if domain.endswith(self.FILEEXT):
            return domain[:-len(self.FILEEXT)]
        else:
            return domain

    def domains(self, locale=None):
        """Returl list of all domain files in values dir"""
        values_dir = locale and "values-{}".format(locale) or "values"
        search = os.path.join(self.basepath, values_dir, self.search)
        return [
            os.path.splitext(os.path.basename(fname))[0]
            for fname in glob.glob(search)
        ]

    def resources(self, locale=None, domain=None):
        """Iterator on resources for given language code (or from values dir)"""
        locale = locale or self.SOURCE_LOCALE
        values_dir = locale != self.SOURCE_LOCALE and "values-{}".format(locale) or "values"
        pattern = domain and "{0}.xml".format(domain) or self.search
        search = os.path.join(self.basepath, values_dir, pattern)
        for source in glob.glob(search):
            (_, fname) = os.path.split(source)
            (domain_file, _) = os.path.splitext(fname)
            xml = etree.parse(source)
            for node in xml.getroot():
                options = {
                    "domain": unicode(domain_file),
                    "locale": unicode(locale)
                }
                if node.tag == 'string':
                    options['message'] = node.text and unicode(node.text) or u""
                    options['name'] = unicode(node.attrib['name'])
                    yield Resource(**options)
                elif node.tag == 'plurals':
                    options['plurals'] = plurals_to_dict(node)
                    options['name'] = unicode(node.attrib['name'])
                    yield Resource(**options)

    def update(self, resources, locale, domain):
        """Save resources by given locale in domain file"""
        if locale == self.SOURCE_LOCALE:
            path = "values/{}.xml".format(domain)
        else:
            path = "values-{}/{}.xml".format(locale, domain)
        filename = os.path.join(self.basepath, path)
        xml = open(filename, 'w')
        # write xml header
        xml.write(XML_START)
        for resource in resources:
            if resource.is_plural:
                xml.write(
                    XML_PLURALS_START.format(resource=resource).encode("utf-8")
                )
                for (quantity, text) in resource.plurals.items():
                    # Write only nonempty plural forms
                    if text != "":
                        xml.write(
                            XML_PLURALS_ITEM.format(
                                quantity=quantity, text=escape(text, APOS)
                            ).encode("utf-8")
                        )
                xml.write(XML_PLURALS_END)
            else:
                # quoteattr text in resource
                resource.message = escape(resource.text, APOS)
                xml.write(XML_STRING.format(resource=resource).encode("utf-8"))
        xml.write(XML_END)
        xml.close()


def get_backend(*args, **kwargs):
    """Required factory"""
    return AndroidXML(*args, **kwargs)
