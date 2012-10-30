#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
from localist import Resource, androidxml


class AndroidXMLTest(unittest.TestCase):
    def setUp(self):
        res_path = os.path.exists("tests") and "tests/android/res" or "android/res"
        self.androidxml = androidxml.get_backend(res_path)
        #remove translated file with "fresh" translations
        fresh_file = os.path.join(res_path, "values-ru/strings-fresh.xml")
        if os.path.exists(fresh_file):
            os.unlink(fresh_file)

    def test_sources(self):
        messages = []
        for msg in self.androidxml.resources():
            messages.append(msg)
        self.assertEqual(len(messages), 4)

    def test_localized_resources(self):
        messages = []
        for msg in self.androidxml.resources(locale="ru"):
            messages.append(msg.text)
        self.assertTrue(u"Первая" in messages)

    def test_locales(self):
        expected_locales = sorted(["en", "ru", "es", "pt-rBR"])
        actual_locales = sorted(self.androidxml.locales())
        self.assertEqual(expected_locales, actual_locales)

    def test_domain_name(self):
        samples = ["strings", "strings-file.xml", "strings-some.file.xml"]
        expected = ["strings", "strings-file", "strings-some.file"]
        actual = [self.androidxml.domain_name(entry) for entry in samples]
        self.assertEqual(actual, expected)

    def test_domains(self):
        expected_domains = ["strings", "strings-fresh"]
        expected_domains.sort()
        actual_domains = self.androidxml.domains()
        actual_domains.sort()
        self.assertEqual(expected_domains, actual_domains)

    def test_update(self):
        # write predefinded messages
        msg_in = Resource(
            domain="strings-fresh",
            message="translated",
            name="fresh_string_one",
            project="test",
            locale="ru"
        )
        self.androidxml.update([msg_in], locale="ru", domain="strings-fresh")
        # read and checkall
        translations = self.androidxml.resources(locale="ru")
        translated = [msg for msg in translations if msg.domain == "strings-fresh"]
        self.assertEqual(translated[0].text, msg_in.text)


if __name__ == '__main__':
    unittest.main()
