#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from localist import Resource
import re


class ResourceTest(unittest.TestCase):
    def setUp(self):
        self.string = "This is a string"
        self.domain = "sample-domain"
        self.name = "key-name"
        self.plurals = {
            "one": "One",
            "other": "Many"
        }
        self.locale = "en"
        self.test_msg = {
            u"type": u"i18n-resource",
            u"locale": self.locale,
            u"message": self.string,
            u"domain": self.domain,
            u"name": self.name,
            u"project": u"default"
        }

    def create_resource(self, text, name=None):
        """Utility function for create resource"""
        return Resource(domain=self.domain, message=text,
                        name=name or self.name, locale=self.locale)

    def test_string(self):
        msg = Resource(
            domain=self.domain, message=self.string,
            name=self.name, locale=self.locale
        )
        self.assertTrue(msg.text == self.string and msg.is_plural is False)

    def test_plurals(self):
        msg = Resource(
            domain=self.domain, plurals=self.plurals,
            name=self.name, locale=self.locale
        )
        self.assertTrue(msg.text == self.plurals['other'] and msg.is_plural)

    def test_conversions(self):
        msg = Resource(**self.test_msg)
        msg_out = json.loads(msg.as_json)
        self.assertEqual(self.test_msg, msg_out)

    def test_assign(self):
        msg = Resource(**self.test_msg)
        msg.message = u'Updated'
        self.assertEqual(msg.text, u'Updated')

    def test_dict(self):
        msg = Resource(**self.test_msg)
        self.assertEqual(self.test_msg, msg.as_dict)

    def test_equality(self):
        res1 = Resource(**self.test_msg)
        res2 = Resource(**self.test_msg)
        res3 = res1
        self.assertTrue(res1 == res2 and res1 is not res2 and res3 is res1)

    def test_notequality(self):
        res1 = Resource(domain="test", message="msg", locale="en", name="key")
        res2 = Resource(domain="test", message="msg", locale="en", name="key1")
        res3 = Resource(domain="test", message="msg1", locale="en", name="key1")
        self.assertTrue(res1 != res2 and res2 != res3 and res1 != res3)

    def test_valid_printf_format(self):
        source = self.create_resource("This is %a source with %s and %d")
        valid_one = self.create_resource("This is a valid with %d and %s")
        valid_next = self.create_resource("Just %s and %d %z")
        formats = [re.compile("%s"), re.compile("%d")]
        self.assertTrue(valid_one.is_same_format(source, formats) and
                        valid_next.is_same_format(source, formats))

    def test_invalid_printf_format(self):
        source = self.create_resource("This is %a source with %s and %d")
        invalid_one = self.create_resource("This is a valid with %d and %d")
        invalid_next = self.create_resource("Just % and % %z")
        formats = [re.compile("%s"), re.compile("%d")]
        self.assertFalse(invalid_one.is_same_format(source, formats) or
                         invalid_next.is_same_format(source, formats))

    def test_valid_mustache_format(self):
        source = self.create_resource("This is a {{resource}} with {{ text }}")
        valid_one = self.create_resource("Valid {{ text }} for {{resource}}")
        formats = [re.compile("{{\s*[a-zA-Z]+\s*}}")]
        self.assertTrue(valid_one.is_same_format(source, formats))

    def test_invalid_mustache_format(self):
        source = self.create_resource("This is a {{resource}} with {{ text }}")
        invalid_one = self.create_resource("Invalid {{text}} for resource")
        invalid_next = self.create_resource("Invalid {{textiy}} for {{ resource}}")
        formats = [re.compile("{{\s*[a-zA-Z]+\s*}}")]
        self.assertFalse(invalid_one.is_same_format(source, formats) or
                         invalid_next.is_same_format(source, formats))

    def test_xml_safety(self):
        valid = self.create_resource("this is a <br /> valid <p>text</p>")
        invalid = self.create_resource("<p> bad <b>broken<a></p> entry</a>")
        self.assertTrue(valid.is_xml_safe() is True and invalid.is_xml_safe() is False)

    def test_xml_with_entities(self):
        valid = self.create_resource("this is a &nbsp; &#37;")
        self.assertTrue(valid.is_xml_safe())

    def test_xml_attr_placeholder(self):
        valid = self.create_resource('<a href="{{ url }}" title="%s">{{test}}</a>')
        self.assertTrue(valid.is_xml_safe())


if __name__ == "__main__":
    unittest.main()
