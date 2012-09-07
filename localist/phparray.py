#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localist import Resource, Backend
import os
import subprocess
import json
from glob import glob


def parse_array(phpdata, varname):
    """Parses an php array assignment"""
    php = subprocess.Popen(
        "php", stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    commands = "{}\nprint(json_encode(${}));".format(phpdata, varname)
    (out, err) = php.communicate(commands)
    out = out.replace(r"\\u", r"\u")
    return json.loads(out)


def serialize_array(data, varname):
    """Serializes dict as php array assignment expr"""
    php = subprocess.Popen(
        "php", stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    js = json.dumps(data)
    commands = "<?php\nvar_export(json_decode('{}', true));".format(js)
    (out, err) = php.communicate(commands)
    return "<?php\n${} = {};".format(varname, out)


def flatten(nested_dict, sep=".", start=""):
    """Flattens nested dict"""
    flat = {}
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
    unflatten = {}
    keys = sorted(flat_dict.keys())
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

    def __init__(self, path, varname, filepattern="*.php"):
        self.path = path
        self.varname = varname
        self.filepattern = filepattern

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

    def resources(self, locale):
        """Yields a resources from php array"""
        search = os.path.join(self.path, locale, self.filepattern)
        for domain_file in glob(search):
            (_, domain) = os.path.split(domain_file)
            (domain, _) = os.path.splitext(domain)
            entries = parse_array(open(domain_file).read(), self.varname)
            entries = entries or {}
            for (key, val) in flatten(entries).items():
                yield Resource(domain=domain, locale=locale, message=val, name=key)

    def update(self, resources, locale, domain):
        """Update a domain in given locale with resources"""
        texts = dict(((res.name, res.message) for res in resources))
        filename = "{}.php".format(domain)
        phpfile = os.path.join(self.path, locale, filename)
        outfile = open(phpfile, "w")
        outfile.write(serialize_array(nested(texts), self.varname))
        #writing lines
        outfile.close()


def get_backend(*args, **kwargs):
    return PHPArray(*args, **kwargs)
