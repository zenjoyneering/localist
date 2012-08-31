#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line script application.
"""

import os
import sys
from ConfigParser import SafeConfigParser
from localist.api import Service


COMMANDS = ["pull", "push"]


def read_config(config):
    """Reads config files in order: /etc/{config}, $HOME/.{config}, .{config}"""
    cfg = SafeConfigParser()
    cfg.read("/etc/{}".format(config))
    cfg.read(os.path.join(os.environ['HOME'], ".{0}".format(config)))
    cfg.read(".{0}".format(config))
    return cfg


def lookup_table(resources, revisions, key_format):
    """Build a lookup table for resources with given key format"""
    lookup = {}
    for res in resources:
        key = key_format.format(resource=res)
        lookup[key] = res
    return lookup


def push(settings, url="default", *args, **kwargs):
    """Push all localizible resources to service"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    print('Pushing {} to {}'.format(project, url))
    service = Service(url)
    source_locale = settings.get('translation', 'source_locale') or 'en'

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = "{resource.name}:{resource.text}"

    pushed = frozenset(
        (lookup_key.format(resource=res)
         for res
         in service.resources(project, source_locale)
        )
    )
    if pushed:
        # TODO: Refactor as a separate *changes* function
        changes = (res
            for res
            in backend.resources()
            if lookup_key.format(resource=res) not in pushed
        )
        revisions = service.update(project, changes)
        # TODO: Update translations too?
        if revisions:
            print("Updated {} resources".format(len(revisions)))
    else:
        print("Making an first push to the workspace""")
        # here we 'cache' list for guarantee that order will not change
        resources = list(backend.resources())
        revisions = service.update(project, resources)
        print("Uploaded {} {} resources".format(len(revisions), source_locale))
        print("Uploading translations...")
        # TODO: Refactor as a separate *translations* function | backend method
        # TODO: Replace domain by source's value, olny for android so must go
        # out
        # TODO: lookup key should be defined by backend
        key = "{resource.name}:{resource.is_plural}"
        source_ids = {}
        for (res, rev) in zip(resources, revisions):
            source_ids[key.format(resource=res)] = (rev, res.domain)
        for locale in backend.locales():
            translations = []
            for res in backend.resources(locale):
                meta = source_ids.get(key.format(resource=res))
                if meta:
                    source, domain = meta
                    res.source = source
                    res.domain = domain
                translations.append(res)
            revisions = service.update(project, translations)
            print("Uploaded {} {} resources".format(len(revisions), locale))


def pull(settings, url="default", *args, **kwargs):
    """Pull all translations for local resources from service"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    print('Pulling {} translations from {}'.format(project, url))
    service = Service(url)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = "{resource.domain}:{resource.name}:{resource.is_plural}"

    to_translate = frozenset(
        (lookup_key.format(resource=res)
         for res
         in backend.resources()
        )
    )
    for locale in backend.locales():
        translations = []
        domain = None
        for res in service.resources(project, locale):
            if lookup_key.format(resource=res) not in to_translate:
                # this key in unknown for local code, skip it
                continue
            if domain and res.domain != domain:
                # the new domain begins, so push current
                print("Updating {} translations for {}".format(locale, domain))
                backend.update(translations, locale, domain)
                translations = []
            translations.append(res)
            domain = res.domain
        # update the last one
        print("Updating {} translations for {}".format(locale, domain))
        backend.update(translations, locale, domain)


def usage(*args, **kwargs):
    print "Available commands: {}".format(", ".join(COMMANDS))


def main():
    settings = read_config("localistrc")
    cmd = len(sys.argv) >= 2 and (sys.argv[1] in COMMANDS) and sys.argv[1] or "usage"
    command = globals()[cmd]
    command(settings, *sys.argv[2:])

if __name__ == "__main__":
    main()
