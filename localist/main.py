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
    domain = domain and backend.domain_name(domain) or None  # *normalize* weird names

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
    if revisions:  # and (not pushed or import_all):
        # TODO: Mark changed messages as obsolete
        print("Uploaded {0} {1} resources".format(len(revisions), source_locale))
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
                    # skip messages without source for now
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


def status(settings, url="default", locale=None, domain=None, verbose=False, *args, **kwargs):
    """Print translation status by domain name"""
    url = settings.get('urls', url) or url
    source_locale = settings.get("translation", "source_locale")
    # this is not needed right now, but should be used, when
    #project = settings.get("translation", "project")
    #if settings.has_section('proxy'):
    #    proxy_opts = dict(settings.items('proxy'))
    #    proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    #else:
    #    proxy = None
    #service = Service(url, proxy=proxy)
    backend_format = settings.get('translation', 'format')
    backend_settings = dict(settings.items(backend_format))
    backend_module = __import__(
        "localist.{0}".format(backend_format), fromlist=["localist"]
    )
    backend = backend_module.get_backend(**backend_settings)
    all_domains = backend.domains(source_locale)
    if domain and not domain in all_domains:
        print("Domain '{}' not found".format(domain))
        return False
    domains = domain and [domain] or all_domains
    all_locales = [lc for lc in backend.locales() if lc != source_locale]
    locales = locale and [locale] or all_locales

    diff_format = "{lc} locale has {count} untranslated messages"
    for domain in domains:
        header = "Translation status for {}".format(domain)
        print(header)
        print("=" * len(header))
        print("")
        avail_keys = []
        messages = {}
        for res in backend.resources(source_locale, domain):
            messages[res.name] = res.text
        avail_keys = frozenset(messages.keys())
        for locale in locales:
            translated_keys = frozenset([r.name for r in backend.resources(locale, domain)])
            diff = avail_keys - translated_keys
            if len(diff) == 0:
                continue
            print(diff_format.format(lc=locale, count=len(diff)))
            if verbose:
                for key in diff:
                    print(u"    - {} ({})".format(key, messages[key]))
                print("")


#TODO Make this extension
def xmllint(settings, url="default", locale=None, *args, **kwargs):
    from lxml.etree import XML
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    service = Service(url, proxy=proxy)
    msg = u"Bad text at {resource.name} from {resource.domain}: {resource.text}"
    for res in service.resources(project, locale or source_locale):
        # check for validity
        try:
            XML('<?xml version="1.0" standalone="yes"?><!DOCTYPE html>\n<div>' + res.text + '</div>')
        except Exception as ex:
            #if not ex.message.startswith("Entity"):
            print("-----------------------")
            print(unicode(ex.message))
            print(msg.format(resource=res))


def validate(settings, url="default", locale=None, domain=None, *args, **kwargs):
    """Validate messages as xml and agains placeholders, defined by regexp"""
    import re
    patterns = [re.compile("%s"), re.compile("%d"), re.compile("{{\s*[$]?[a-zA-Z]+\s*}}")]
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    service = Service(url, proxy=proxy)
    #backend_format = settings.get('translation', 'format')
    #backend_settings = dict(settings.items(backend_format))
    #backend_module = __import__(
    #    "localist.{0}".format(backend_format), fromlist=["localist"]
    #)
    #backend = backend_module.get_backend(**backend_settings)
    msg_format = u" - Template miss in {res.domain}: {res.name} => {res.text}"
    xml_invalid_format = u" - Broken XML in {res.domain}: {res.name} = {res.text}"
    sources = {}
    # get resources in source_locale from service
    for res in service.resources(project, source_locale, domain):
        sources[res._id] = res
    # get translations for chozen locale
    failures = 0
    for res in service.resources(project, locale, domain):
        if not res.source['id'] in sources:
            print("Wut?!!! {} | {}".format(domain, res.name))
            continue
        if not res.is_same_format(sources[res.source['id']], patterns):
            print(msg_format.format(res=res))
            failures += 1
        if not res.is_xml_safe():
            print(xml_invalid_format.format(res=res))
            failures += 1
    print("------------------")
    print("{} failures".format(failures))


def check(settings, url="default", locale=None, *args, **kwargs):
    """Count all translation duplicates"""
    url = settings.get('urls', url) or url
    project = settings.get("translation", "project")
    source_locale = settings.get("translation", "source_locale")
    if settings.has_section('proxy'):
        proxy_opts = dict(settings.items('proxy'))
        proxy = (proxy_opts.get('host'), proxy_opts.get('port', 80))
    else:
        proxy = None
    service = Service(url, proxy=proxy)
    texts = {}
    sources = {}
    for res in service.resources(project, source_locale):
        sources[res._id] = []
        texts[res._id] = res.text
    for res in service.resources(project, locale):
        sources[res.source['id']].append(res._id)
        texts[res._id] = res.text
    for (k, v) in sources.items():
        if len(v) > 1:
            print("Mutiple translations for {}:".format(k))
            print(texts[k])
            for i in v:
                print(u" *. {}\n  {}\n".format(i, texts[i]))
            print("---------------------\n")


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

    status_parser = subparsers.add_parser('status', help=status.__doc__)
    status_parser.add_argument('-d', '--domain', help="domain to check")
    status_parser.add_argument('-l', '--locale', help="locale to pull")
    status_parser.add_argument('-v', '--verbose', action="store_true", help="verbose")
    status_parser.set_defaults(func=status)

    subparsers.add_parser('stats', help=stats.__doc__).set_defaults(func=stats)
    subparsers.add_parser('diff', help=diff.__doc__).set_defaults(func=diff)

    # this is a *very* dangerous command
    #drop_parser = subparsers.add_parser('drop', help=drop.__doc__)
    #drop_parser.add_argument('-d', '--domain', help="domain to delete")
    #drop_parser.add_argument('-l', '--locale', help="locale to delete")
    #drop_parser.set_defaults(func=drop)

    lint_parser = subparsers.add_parser('xmllint')
    lint_parser.add_argument('-l', '--locale')
    lint_parser.set_defaults(func=xmllint)

    validation_parser = subparsers.add_parser('validate')
    validation_parser.add_argument('-l', '--locale')
    validation_parser.add_argument('-d', '--domain')
    validation_parser.set_defaults(func=validate)

    chk_parser = subparsers.add_parser('check')
    chk_parser.add_argument('-l', '--locale')
    chk_parser.set_defaults(func=check)

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
