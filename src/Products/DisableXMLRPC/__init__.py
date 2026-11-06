# -*- coding: utf-8 -*-
from Products.DisableXMLRPC.patch import apply_patch


apply_patch()


def initialize(context):
    """Zope 2 product initializer (nothing to register)."""
