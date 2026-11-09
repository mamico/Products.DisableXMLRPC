# -*- coding: utf-8 -*-
"""Backport of Zope 5.13's ``enable-xmlrpc`` directive for older Zope versions.

Zope (2.13, 4.x and 5.x < 5.13) handles XML-RPC inside
``ZPublisher.HTTPRequest.HTTPRequest.processInputs`` by calling
``xmlrpc.parse_input`` / ``xmlrpc.response`` through the module global
``ZPublisher.HTTPRequest.xmlrpc``:

* Zope2 2.13 lazily imports ``ZPublisher.xmlrpc`` into that global only
  when it is still ``None``;
* Zope 4/5 import it at module level.

Replacing that global with ``XmlrpcProxy`` lets us refuse XML-RPC requests
with the same ``BadRequest('Unsupported request type')`` raised by
Zope >= 5.13, without touching ``processInputs`` itself.
"""
import logging
import os


logger = logging.getLogger('Products.DisableXMLRPC')

ENV_VAR = 'ZOPE_ENABLE_XMLRPC'
PRODUCT_CONFIG_SECTION = 'disable-xmlrpc'
PRODUCT_CONFIG_KEY = 'enable-xmlrpc'

_TRUE = ('1', 'on', 'true', 'yes')
_FALSE = ('0', 'off', 'false', 'no')

# original value of ZPublisher.HTTPRequest.xmlrpc (None on Zope2 2.13)
_original = []


def _as_bool(value):
    """Convert a config value to a boolean, ``None`` if not recognised."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    return None


def _product_config_value():
    try:
        from App.config import getConfiguration
    except ImportError:  # pragma: no cover
        return None
    product_config = getattr(getConfiguration(), 'product_config', None) or {}
    section = product_config.get(PRODUCT_CONFIG_SECTION) or {}
    return section.get(PRODUCT_CONFIG_KEY)


def core_zope_value():
    try:
        from App.config import getConfiguration
    except ImportError:  # pragma: no cover
        return None
    return getattr(getConfiguration(), 'enable_xmlrpc', None)


def xmlrpc_enabled():
    """Return True if Zope's built-in XML-RPC support should be used.

    Precedence: environment variable, then ``<product-config disable-xmlrpc>``
    in zope.conf, then the default (disabled).
    """
    value = _as_bool(os.environ.get(ENV_VAR))
    if value is not None:
        return value
    value = _as_bool(_product_config_value())
    if value is not None:
        return value
    return False


class XmlrpcProxy(object):
    """Stand-in for the ``ZPublisher.xmlrpc`` module."""

    def _module(self):
        from ZPublisher import xmlrpc
        return xmlrpc

    def parse_input(self, data):
        if not xmlrpc_enabled():
            from zExceptions import BadRequest
            raise BadRequest('Unsupported request type')
        return self._module().parse_input(data)

    def response(self, response):
        return self._module().response(response)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return getattr(self._module(), name)


def has_native_support():
    """True for Zope >= 5.13, where ``enable-xmlrpc`` exists in zope.conf."""
    from ZPublisher.HTTPRequest import HTTPRequest
    func = HTTPRequest.processInputs
    func = getattr(func, '__func__', func)  # py2 unbound method
    return 'enable_xmlrpc' in func.__code__.co_names


def is_patched():
    from ZPublisher import HTTPRequest
    return isinstance(getattr(HTTPRequest, 'xmlrpc', None), XmlrpcProxy)


def apply_patch():
    """Install the proxy. Idempotent; no-op on Zope >= 5.13."""
    from ZPublisher import HTTPRequest
    if has_native_support():
        logger.info(
            'Zope supports the "enable-xmlrpc" directive natively (currently: %s): '
            'Products.DisableXMLRPC does nothing, use "enable-xmlrpc off" '
            'in zope.conf instead.',
            'on' if core_zope_value() else 'off',
        ),
        return False
    if is_patched():
        return False
    _original.append(getattr(HTTPRequest, 'xmlrpc', None))
    HTTPRequest.xmlrpc = XmlrpcProxy()
    logger.info(
        'XML-RPC support patched (currently %s). Configure it with '
        '<product-config %s> %s on|off </product-config> or the %s '
        'environment variable.',
        'enabled' if xmlrpc_enabled() else 'disabled',
        PRODUCT_CONFIG_SECTION, PRODUCT_CONFIG_KEY, ENV_VAR)
    return True


def remove_patch():
    """Restore the original ``ZPublisher.HTTPRequest.xmlrpc`` (for tests)."""
    from ZPublisher import HTTPRequest
    if is_patched():
        HTTPRequest.xmlrpc = _original.pop() if _original else None
