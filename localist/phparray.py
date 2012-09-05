#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localist import Resource, Backend
import os
import json
import re
from glob import glob


def parse_array(php):
    """Parses an php array assignment"""
    js = php.replace("=>", ":").replace("<?php", "").replace("<?", "")
    js = js.replace(");", "}").replace(")", "}").replace("array(", "{")
    js = re.sub("[$][a-zA-Z0-9_]*\s*=\s*", "", js)
    js = re.sub("[,]\s*[}]", "}", js)
    return json.loads(js)


def serialize_array(data, varname):
    """Serializes dict as php array assignment expr"""
    js = json.dumps(data, indent=1)
    js = js.replace("{", "array(").replace("}", ")").replace(":", "=>")
    return "<?php\n${} = {};".format(varname, js)


def flatten(nested_dict, sep=".", start=""):
    """Flattens nested dict"""
    flat = {}
    for (k, v) in nested_dict.items():
        key = start and "".join((start, sep, k)) or k
        if isinstance(v, dict):
            flat.update(flatten(v, start=key))
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
            entries = parse_array(open(domain_file).read())
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
