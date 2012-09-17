#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line script application.
"""

import os
import sys
from ConfigParser import SafeConfigParser
from localist.api import Service


COMMANDS = ["pull", "push", "stats"]


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
    source_locale = settings.get('translation', 'source_locale')
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    print('Pushing {} to {}'.format(project, url))
    service = Service(url, proxy=proxy)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = u"{resource.name}:{resource.text}"

    # ensure if project info exists, create if not
    project_info = service.project_info(project)
    if not project_info:
        #creating project
        translations = [
            locale for locale in backend.locales()
            if locale != source_locale
        ]
        service.register_project(project, source_locale, translations)

    pushed = frozenset((
        lookup_key.format(resource=res)
        for res
        in service.resources(project, source_locale)
    ))
    if pushed:
        # TODO: Refactor as a separate *changes* function
        changes = (
            res for res in backend.resources(source_locale)
            if lookup_key.format(resource=res) not in pushed
        )
        revisions = service.update(project, changes)
        # TODO: Update translations too?
        if revisions:
            print("Updated {} resources".format(len(revisions)))
    else:
        print("Making an first push to the workspace""")
        # here we 'cache' list for guarantee that order will not change
        resources = list(backend.resources(source_locale))
        revisions = service.update(project, resources)
        print("Uploaded {} {} resources".format(len(revisions), source_locale))
        print("Uploading translations...")
        # TODO: Refactor as a separate *translations* function | backend method
        # TODO: Replace domain by source's value, olny for android so must go
        # out
        # TODO: lookup key should be defined by backend
        key = u"{resource.name}:{resource.is_plural}"
        source_ids = {}
        for (res, rev) in zip(resources, revisions):
            source_ids[key.format(resource=res)] = (rev, res.domain)
        locales = (locale for locale in backend.locales() if locale != source_locale)
        for locale in locales:
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
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    print('Pulling {} translations from {}'.format(project, url))
    service = Service(url, proxy=proxy)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = u"{resource.domain}:{resource.name}:{resource.is_plural}"

    to_translate = dict((
        (lookup_key.format(resource=res), res)
        for res in backend.resources(locale=source_locale)
    ))
    # for every resource from server if it's text same as local
    # save source doc id to choose right one from translations
    sources = {}
    for res in service.resources(project, source_locale):
        key = lookup_key.format(resource=res)
        if to_translate.get(key, None) == res:
            sources[key] = {'id': res._id, 'rev': res._rev}

    for locale in backend.locales():
        translated = []
        domain = None
        translations = (
            res for res in service.resources(project, locale)
            if sources.get(lookup_key.format(resource=res), None) == res.source
        )
        for res in translations:
            if domain and res.domain != domain and translated:
                # the new domain begins, so push current
                print("Updating {} translations for {}".format(locale, domain))
                backend.update(translated, locale, domain)
                translated = []
            translated.append(res)
            domain = res.domain
        if domain and translated:
            # update the last one
            print("Updating {} translations for {}".format(locale, domain))
            backend.update(translated, locale, domain)


def stats(settings, *args, **kwrags):
    """Display duplacation stats on resources"""
    project = settings.get("translation", "project")
    title = "Statistics on {}".format(project)
    print(title)
    print("=" * len(title))
    print("")
    source_locale = settings.get("translation", "source_locale")
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)
    text_to_key = {}
    total = 0
    for res in backend.resources(locale=source_locale):
        if res.text not in text_to_key:
            text_to_key[res.text] = []
        text_to_key[res.text].append(res)
        total += 1
    print("{} messages in project".format(total))
    print("")
    repeats = {}
    for text, dups in text_to_key.items():
        count = len(dups)
        if count > 1:
            if not count in repeats:
                repeats[count] = 0
            repeats[count] += 1

    for r in sorted(repeats.keys()):
        count = repeats[r]
        print("{} messages repeated {} times ({}%)".format(count, r, (count * 100 / total)))


def usage(*args, **kwargs):
    print "Available commands: {}".format(", ".join(COMMANDS))


def main():
    settings = read_config("localistrc")
    cmd = len(sys.argv) >= 2 and (sys.argv[1] in COMMANDS) and sys.argv[1] or "usage"
    command = globals()[cmd]
    command(settings, *sys.argv[2:])

if __name__ == "__main__":
    main()
