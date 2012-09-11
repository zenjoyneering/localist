#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest
#from localist import Resource
from localist.phparray import *

PHP_ARR = """<?php

$some_var = array(
    "key" => "value",
    "nested" => array(
        "nk" => "inner_val",
        "more" => array("new_level" => 300)
    ),
    "more_k" => "and end",
    "list" => array("one", "two", "three")
);

"""

PY_ARR = {
    "key": "value",
    "nested": {
        "nk": "inner_val",
        "more": {
            "new_level": 300
        }
    },
    "more_k": "and end",
    "list": ["one", "two", "three"]
}


class PHPArrayTest(unittest.TestCase):

    def setUp(self):
        res_path = os.path.exists("tests") and "tests/phparray/loclist" or "phparray/loclist"
        self.phparr = PHPArray(res_path, varname="list")

    def tearDown(self):
        res_path = os.path.exists("tests") and "tests/phparray/loclist" or "phparray/loclist"
        translations = os.path.join(res_path, "es_ES", "first.list.php")
        if os.path.exists(translations):
            os.unlink(translations)

    def test_parse(self):
        parsed = parse_array(PHP_ARR, "some_var")
        self.assertEqual(parsed, PY_ARR)

    def test_serialize_parse(self):
        serialized = serialize_array(PY_ARR, "some_var")
        self.assertEqual(PY_ARR, parse_array(serialized, "some_var"))

    def test_flatten(self):
        orig = {
            "first": 1,
            "second": "100",
            "nested": {
                "more": "one",
                "yet": "level",
                "inner": {
                    "deepest": "inside"
                }
            },
            "list": ["one", "two", "three"],
            "last": 100
        }
        flat = flatten(orig)
        expected = {
            "first": 1,
            "second": "100",
            "nested.more": "one",
            "nested.yet": "level",
            "nested.inner.deepest": "inside",
            "list.0": "one",
            "list.1": "two",
            "list.2": "three",
            "last": 100
        }
        self.assertEqual(flat, expected)

    def test_nested(self):
        flat = {
            "first": 1,
            "second": "100",
            "nested.more": "one",
            "nested.yet": "level",
            "nested.inner.deepest": "inside",
            "last": 100
        }
        expected = {
            "first": 1,
            "second": "100",
            "nested": {
                "more": "one",
                "yet": "level",
                "inner": {
                    "deepest": "inside"
                }
            },
            "last": 100
        }
        self.assertEqual(nested(flat), expected)

    def test_locales(self):
        expected = sorted(["ru_RU", "en_US", "es_ES"])
        actual = sorted(self.phparr.locales())
        self.assertEqual(expected, actual)

    def test_domains(self):
        expected = sorted(["first.list", "second.list"])
        actual = sorted(self.phparr.domains("ru_RU"))
        self.assertEqual(expected, actual)

    def test_resources(self):
        expected_keys = sorted([
            "simple_name", "we.need.to_go", "we.need.to_be", "we.should",
            "more", "yet"
        ])
        actual_keys = [resource.name for resource in self.phparr.resources("ru_RU")]
        self.assertEqual(expected_keys, sorted(actual_keys))

    def test_update(self):
        resources = [
            res for res in self.phparr.resources("ru_RU")
            if res.domain == "first.list"
        ]
        expected = sorted([
            (res.name, res.text)
            for res in resources
        ])
        self.phparr.update(resources, "es_ES", "first.list")
        actual = sorted([
            (res.name, res.text)
            for res in self.phparr.resources("es_ES")
        ])
        self.assertTrue(len(resources) > 0 and expected == actual)


if __name__ == "__main__":
    unittest.main()
