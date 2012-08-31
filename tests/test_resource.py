#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from localist import Resource


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


if __name__ == "__main__":
    unittest.main()
