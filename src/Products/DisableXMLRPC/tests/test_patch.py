# -*- coding: utf-8 -*-
import os
import unittest
from io import BytesIO

from Products.DisableXMLRPC import patch


XMLRPC_CALL = b"""<?xml version="1.0"?>
<methodCall>
  <methodName>examples.getStateName</methodName>
  <params>
    <param><value><i4>41</i4></value></param>
  </params>
</methodCall>
"""

NATIVE = patch.has_native_support()


class ConfigMixin(object):

    def setUp(self):
        from App.config import getConfiguration
        self.config = getConfiguration()
        self._env = os.environ.pop(patch.ENV_VAR, None)
        self._product_config = getattr(self.config, 'product_config', None)
        self.config.product_config = {}

    def tearDown(self):
        os.environ.pop(patch.ENV_VAR, None)
        if self._env is not None:
            os.environ[patch.ENV_VAR] = self._env
        if self._product_config is None:
            del self.config.product_config
        else:
            self.config.product_config = self._product_config

    def set_product_config(self, value):
        self.config.product_config = {
            patch.PRODUCT_CONFIG_SECTION: {patch.PRODUCT_CONFIG_KEY: value},
        }


class TestXmlrpcEnabled(ConfigMixin, unittest.TestCase):

    def test_default_is_disabled(self):
        self.assertFalse(patch.xmlrpc_enabled())

    def test_product_config_on(self):
        self.set_product_config('on')
        self.assertTrue(patch.xmlrpc_enabled())

    def test_product_config_off(self):
        self.set_product_config('off')
        self.assertFalse(patch.xmlrpc_enabled())

    def test_product_config_garbage_falls_back_to_default(self):
        self.set_product_config('maybe')
        self.assertFalse(patch.xmlrpc_enabled())

    def test_env_on(self):
        os.environ[patch.ENV_VAR] = 'on'
        self.assertTrue(patch.xmlrpc_enabled())

    def test_env_wins_over_product_config(self):
        self.set_product_config('on')
        os.environ[patch.ENV_VAR] = 'false'
        self.assertFalse(patch.xmlrpc_enabled())
        self.set_product_config('off')
        os.environ[patch.ENV_VAR] = 'TRUE'
        self.assertTrue(patch.xmlrpc_enabled())

    def test_no_product_config_attribute(self):
        del self.config.product_config
        self.assertFalse(patch.xmlrpc_enabled())
        self.config.product_config = {}


@unittest.skipIf(NATIVE, 'Zope >= 5.13 supports enable-xmlrpc natively')
class TestPatchedRequest(ConfigMixin, unittest.TestCase):

    def setUp(self):
        super(TestPatchedRequest, self).setUp()
        patch.apply_patch()

    def _makeRequest(self, body, content_type):
        from ZPublisher.HTTPRequest import HTTPRequest
        from ZPublisher.HTTPResponse import HTTPResponse
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': str(len(body)),
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080',
        }
        response = HTTPResponse(stdout=BytesIO())
        return HTTPRequest(BytesIO(body), environ, response)

    def test_is_patched(self):
        self.assertTrue(patch.is_patched())

    def test_apply_patch_is_idempotent(self):
        from ZPublisher import HTTPRequest
        proxy = HTTPRequest.xmlrpc
        self.assertFalse(patch.apply_patch())
        self.assertIs(HTTPRequest.xmlrpc, proxy)

    def test_xmlrpc_disabled(self):
        from zExceptions import BadRequest
        req = self._makeRequest(XMLRPC_CALL, 'text/xml')
        with self.assertRaises(BadRequest) as cm:
            req.processInputs()
        self.assertIn('Unsupported request type', str(cm.exception))

    def _assert_xmlrpc_processed(self, req):
        req.processInputs()
        self.assertEqual(req.args, (41,))
        self.assertTrue(
            req.other['PATH_INFO'].endswith('/examples/getStateName'))
        self.assertEqual(
            req.response.__class__.__module__, 'ZPublisher.xmlrpc')

    def test_xmlrpc_enabled_by_product_config(self):
        self.set_product_config('on')
        req = self._makeRequest(XMLRPC_CALL, 'text/xml')
        self._assert_xmlrpc_processed(req)

    def test_xmlrpc_enabled_by_env(self):
        os.environ[patch.ENV_VAR] = '1'
        req = self._makeRequest(XMLRPC_CALL, 'text/xml')
        self._assert_xmlrpc_processed(req)

    def test_form_post_unaffected(self):
        req = self._makeRequest(
            b'foo=bar', 'application/x-www-form-urlencoded')
        req.processInputs()
        self.assertEqual(req.form['foo'], 'bar')

    def test_xml_post_not_xmlrpc_without_text_xml(self):
        req = self._makeRequest(XMLRPC_CALL, 'application/xml')
        req.processInputs()
        self.assertEqual(
            req.response.__class__.__module__, 'ZPublisher.HTTPResponse')

    def test_remove_patch(self):
        from ZPublisher import HTTPRequest
        patch.remove_patch()
        try:
            self.assertFalse(patch.is_patched())
            self.assertFalse(isinstance(HTTPRequest.xmlrpc, patch.XmlrpcProxy))
        finally:
            patch.apply_patch()


@unittest.skipUnless(NATIVE, 'only for Zope >= 5.13')
class TestNativeSupport(unittest.TestCase):

    def test_patch_not_applied(self):
        self.assertFalse(patch.apply_patch())
        self.assertFalse(patch.is_patched())
