#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line script application.
"""

import os
from ConfigParser import SafeConfigParser
from localist.api import Service
import argparse

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


def read_config(config):
    """Reads config files in order: /etc/{config}, $HOME/.{config}, .{config}"""
    cfg = SafeConfigParser()
    cfg.read("/etc/{0}".format(config))
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


def push(settings, url="default", domain=None, import_all=False, *args, **kwargs):
    """Push all localizible resources to service"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get('translation', 'source_locale')
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    print('Pushing {0}'.format(project))
    service = Service(url, proxy=proxy)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{0}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = u"{resource.domain}:{resource.name}:{resource.text}"

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
        in service.resources(project, source_locale, domain)
    ))
    if pushed:
        # TODO: Refactor as a separate *changes* function
        changes = [
            res for res in backend.resources(source_locale, domain)
            if lookup_key.format(resource=res) not in pushed
        ]
        revisions = service.update(project, changes)
    else:
        print("Making an first push to the workspace""")
        # here we 'cache' list for guarantee that order will not change
        changes = list(backend.resources(source_locale, domain))
        revisions = service.update(project, changes)
    if revisions:
        print("Uploaded {0} {1} resources".format(len(revisions), source_locale))
    if revisions and (not pushed or import_all):
        print("Uploading translations...")
        # TODO: Refactor as a separate *translations* function | backend method
        # TODO: Replace domain by source's value, olny for android so must go
        # out
        # TODO: lookup key should be defined by backend
        key = u"{resource.domain}.{resource.name}:{resource.is_plural}"
        source_ids = {}
        for (res, rev) in zip(changes, revisions):
            source_ids[key.format(resource=res)] = (rev, res.domain)
        locales = (locale for locale in backend.locales() if locale != source_locale)
        for locale in locales:
            translations = []
            for res in backend.resources(locale, domain):
                meta = source_ids.get(key.format(resource=res))
                if meta:
                    (res.source, res.domain) = meta
                translations.append(res)
            revisions = service.update(project, translations)
            print("Uploaded {0} {1} resources".format(len(revisions), locale))


def pull(settings, url="default", locale=None, domain=None, *args, **kwargs):
    """Pull all translations for local resources from service"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    print('Pulling {0} translations'.format(project))
    service = Service(url, proxy=proxy)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{0}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = u"{resource.domain}:{resource.name}:{resource.is_plural}"

    to_translate = OrderedDict((
        (lookup_key.format(resource=res), res)
        for res in backend.resources(source_locale, domain)
    ))
    # for every resource from server if it's text same as local
    # save source doc id to choose right one from translations
    sources = {}
    for res in service.resources(project, source_locale):
        key = lookup_key.format(resource=res)
        if to_translate.get(key, None) == res:
            sources[key] = {'id': res._id, 'rev': res._rev}

    locale_list = locale and [locale] or [loc for loc in backend.locales() if loc != source_locale]
    for locale in locale_list:
        translations = {}
        for res in service.resources(project, locale, domain):
            lookup = lookup_key.format(resource=res)
            if sources.get(lookup, None) == res.source:
                translations[lookup] = res
        translated = []
        current_domain = None
        for (key, source) in to_translate.items():
            res = translations.get(key, None)
            if res is None:
                continue
            if current_domain and res.domain != current_domain and translated:
                # the new domain begins, so push current
                backend.update(translated, locale, current_domain)
                translated = []
            translated.append(res)
            current_domain = res.domain
        # update the last one
        if current_domain and translated:
            backend.update(translated, locale, current_domain)


def diff(settings, url="default", *args, **kwargs):
    """Show differences betwen local and service translations"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    print('Getting diff for {0} sources'.format(project))
    service = Service(url, proxy=proxy)

    # instantiating backend
    # TODO: Refactor this, make extendable.
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{0}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)

    lookup_key = u"{resource.domain}:{resource.name}:{resource.text}"

    local_sources = frozenset((
        lookup_key.format(resource=res)
        for res in backend.resources(locale=source_locale)
    ))
    service_sources = frozenset((
        lookup_key.format(resource=res)
        for res in service.resources(project, source_locale)
    ))
    print("New local resources:")
    print(local_sources - service_sources)

    print("New remote resources:")
    print(service_sources - local_sources)

    for locale in backend.locales():
        print("Getting diff for {0} translations".format(locale))
        local_sources = frozenset((
            lookup_key.format(resource=res)
            for res in backend.resources(locale=locale)
        ))
        service_sources = frozenset((
            lookup_key.format(resource=res)
            for res in service.resources(project, locale)
        ))
        local_new = sorted(local_sources - service_sources)
        print("Local unique resources: {0}".format(len(local_new)))
        remote_new = sorted(service_sources - local_sources)
        print("Remote unique resources: {0}".format(len(remote_new)))


def stats(settings, *args, **kwrags):
    """Display duplication stats on resources"""
    project = settings.get("translation", "project")
    title = "Statistics on {0}".format(project)
    print(title)
    print("=" * len(title))
    print("")
    source_locale = settings.get("translation", "source_locale")
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{0}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)
    text_to_key = {}
    total = 0
    for res in backend.resources(locale=source_locale):
        if res.text not in text_to_key:
            text_to_key[res.text] = []
        text_to_key[res.text].append(res)
        total += 1
    print("{0} messages in project".format(total))
    for locale in backend.locales():
        resources = [res for res in backend.resources(locale=locale)]
        print ("{0} translation for {1} locale".format(len(resources), locale))
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
        print("{0} messages repeated {1} times ({2}%)".format(count, r, (count * 100 / total)))

    print("")
    print("Checking for keys, available only in translations and not in sources")
    lookup = u"{resource.domain}:{resource.name}:{resource.is_plural}"
    source_keys = frozenset((
        lookup.format(resource=res)
        for res in backend.resources(locale=source_locale)
    ))
    total = 0
    for locale in backend.locales():
        for res in backend.resources(locale=locale):
            if not lookup.format(resource=res) in source_keys:
                #print(u"Resource {resource.name} from {resource.locale} not found in {resource.domain}".format(resource=res))
                total += 1
    print("===============")
    print("Total {0} keys seem to be deprecated and will be removed on next pull".format(total))


def drop(settings, url="default", locale=None, domain=None, *args, **kwargs):
    """Drop all strings in given domain from service"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    locale_to_delete = locale or settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    service = Service(url, proxy=proxy)
    revs = service.drop(project, locale_to_delete, domain)
    print("{0} messages deleted from service".format(len(revs)))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    push_parser = subparsers.add_parser('push', help=push.__doc__)
    push_parser.add_argument('-d', '--domain', help="domain to push")
    push_parser.set_defaults(func=push)

    pull_parser = subparsers.add_parser('pull', help=pull.__doc__)
    pull_parser.add_argument('-l', '--locale', help="locale to pull")
    pull_parser.add_argument('-d', '--domain', help="domain to push")
    pull_parser.set_defaults(func=pull)

    subparsers.add_parser('stats', help=stats.__doc__).set_defaults(func=stats)
    subparsers.add_parser('diff', help=diff.__doc__).set_defaults(func=diff)

    drop_parser = subparsers.add_parser('drop', help=drop.__doc__)
    drop_parser.add_argument('-d', '--domain', help="domain to delete")
    drop_parser.add_argument('-l', '--locale', help="locale to delete")
    drop_parser.set_defaults(func=drop)

    opts = parser.parse_args()
    settings = read_config("localistrc")
    opts.func(settings, **vars(opts))

    """
    parser.add_argument('command')
    parser.add_argument('-l', '--locale')
    parser.add_argument('-d', '--domain')
    settings = read_config("localistrc")
    cmd = len(sys.argv) >= 2 and (sys.argv[1] in COMMANDS) and sys.argv[1] or "usage"
    command = globals()[cmd]
    opts = vars(parser.parse_args())
    command(settings, **opts)
    """

if __name__ == "__main__":
    main()
