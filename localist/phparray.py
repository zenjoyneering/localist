#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localist import Resource, Backend
import os
import subprocess
import json
from glob import glob
from collections import OrderedDict
import re

ARRAY_BEAUTIFY = {
    "from": re.compile("=>\s*array\s?[(]"),
    "to": "=> array("
}


def parse_array(phpdata, varname, php_bin="php"):
    """Parses an php array assignment"""
    php = subprocess.Popen(
        php_bin, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    commands = "{}\nprint(json_encode(${}));".format(phpdata, varname)
    (out, err) = php.communicate(commands)
    if err:
        print err
        return {}
    return json.loads(out, object_pairs_hook=OrderedDict)


def serialize_array(data, varname, php_bin="php"):
    """Serializes dict as php array assignment expr"""
    php = subprocess.Popen(
        php_bin, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    #js = json.dumps(data).replace("'", r"\'").replace('\\\\', '\\')
    #js = re.sub(r"[^\\]'", r"\'", json.dumps(data))
    js = json.dumps(data).replace("''", r'\"').encode('string_escape')
    commands = """<?php\nvar_export(json_decode('{}', true));""".format(js)
    (out, err) = php.communicate(commands)
    if err:
        print err
    out = re.sub(ARRAY_BEAUTIFY['from'], ARRAY_BEAUTIFY['to'], out)
    return "<?php\n${} = {};".format(varname, out)


def flatten(nested_dict, sep=".", start=""):
    """Flattens nested dict"""
    flat = OrderedDict()
    for (k, v) in nested_dict.items():
        key = start and u"".join((start, sep, unicode(k))) or k
        if isinstance(v, dict):
            flat.update(flatten(v, start=key))
        elif isinstance(v, list):
            flat.update(flatten(dict(enumerate(v)), start=key))
        else:
            flat[key] = v
    return flat


def nested(flat_dict, sep="."):
    """Make nested dict from flattened, using `sep` as key separator"""
    unflatten = OrderedDict()
    keys = flat_dict.keys()
    for key in keys:
        parts = key.split(sep)
        if len(parts) == 1:
            # simple str value
            unflatten[parts[0]] = flat_dict[key]
        else:
            level = unflatten
            for part in parts[:-1]:
                if not part in level:
                    level[part] = {}
                level = level[part]
            level[parts[-1]] = flat_dict[key]
    return unflatten


class PHPArray(Backend):
    """PHP key-value arrays backed l10n resource storage"""
    LOCALE_DIR = "??_??"

    def __init__(self, path, varname, filepattern="*.php", exclude=None, php_bin="php"):
        self.path = path
        self.varname = varname
        self.filepattern = filepattern
        self.php_bin = php_bin
        if exclude:
            self.exclude = [it.strip() for it in exclude.split(',') if it]
        else:
            self.exclude = []

    def locales(self):
        """Generator returning avaialble"""
        search = os.path.join(self.path, self.LOCALE_DIR)
        for dirname in glob(search):
            (_, locale_code) = os.path.split(dirname)
            yield locale_code

    def domains(self, locale):
        """Domains for given project"""
        search = os.path.join(self.path, locale, self.filepattern)
        return [
            os.path.splitext(os.path.basename(fname))[0]
            for fname
            in glob(search)
        ]

    def resources(self, locale, domain=None):
        """Yields a resources from php array"""
        pattern = domain and domain + self.filepattern or self.filepattern
        search = os.path.join(self.path, locale, pattern)
        for domain_file in glob(search):
            (_, domain) = os.path.split(domain_file)
            if domain in self.exclude:
                # domain is excluded, so just skip
                continue
            (domain, _) = os.path.splitext(domain)
            if domain in self.exclude:
                # domain is excluded, so just skip
                continue
            entries = parse_array(open(domain_file).read(), self.varname, self.php_bin)
            entries = entries or {}
            for (key, val) in flatten(entries).items():
                yield Resource(domain=domain, locale=locale, message=val, name=key)

    def update(self, resources, locale, domain):
        """Update a domain in given locale with resources"""
        texts = OrderedDict(((res.name, res.message) for res in resources))
        filename = "{}.php".format(domain)
        phpfile = os.path.join(self.path, locale, filename)
        # write
        outfile = open(phpfile, "w")
        outfile.write(serialize_array(nested(texts), self.varname, self.php_bin))
        outfile.close()


def get_backend(*args, **kwargs):
    return PHPArray(*args, **kwargs)
