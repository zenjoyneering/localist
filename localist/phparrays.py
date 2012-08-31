#!/usr/bin/env python
# -*- coding: utf-8 -*-

from localist import Resource, Backend


class PHPArrays(Backend):
    """PHP ke-value arrays backed l10n resource storage"""

    def __init__(self, path, varname, filepattern):
        self.path = path
        self.varname = varname
        self.filepattern = filepattern
