# -*- coding: utf-8 -*-
# Copyright 2019 New Vector Ltd
# Copyright 2019 Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import yaml

from synapse.config.server import ServerConfig, is_threepid_reserved

from tests import unittest


class ServerConfigTestCase(unittest.TestCase):
    def test_is_threepid_reserved(self):
        user1 = {"medium": "email", "address": "user1@example.com"}
        user2 = {"medium": "email", "address": "user2@example.com"}
        user3 = {"medium": "email", "address": "user3@example.com"}
        user1_msisdn = {"medium": "msisdn", "address": "447700000000"}
        config = [user1, user2]

        self.assertTrue(is_threepid_reserved(config, user1))
        self.assertFalse(is_threepid_reserved(config, user3))
        self.assertFalse(is_threepid_reserved(config, user1_msisdn))

    def test_unsecure_listener_no_listeners_open_private_ports_false(self):
        conf = yaml.safe_load(
            ServerConfig().generate_config_section(
                "che.org", "/data_dir_path", False, None
            )
        )

        expected_listeners = [
            {
                "port": 8008,
                "tls": False,
                "type": "http",
                "x_forwarded": True,
                "bind_addresses": ["::1", "127.0.0.1"],
                "resources": [{"names": ["client", "federation"], "compress": False}],
            }
        ]

        self.assertEqual(conf["listeners"], expected_listeners)

    def test_unsecure_listener_no_listeners_open_private_ports_true(self):
        conf = yaml.safe_load(
            ServerConfig().generate_config_section(
                "che.org", "/data_dir_path", True, None
            )
        )

        expected_listeners = [
            {
                "port": 8008,
                "tls": False,
                "type": "http",
                "x_forwarded": True,
                "resources": [{"names": ["client", "federation"], "compress": False}],
            }
        ]

        self.assertEqual(conf["listeners"], expected_listeners)

    def test_listeners_set_correctly_open_private_ports_false(self):
        listeners = [
            {
                "port": 8448,
                "resources": [{"names": ["federation"]}],
                "tls": True,
                "type": "http",
            },
            {
                "port": 443,
                "resources": [{"names": ["client"]}],
                "tls": False,
                "type": "http",
            },
        ]

        conf = yaml.safe_load(
            ServerConfig().generate_config_section(
                "this.one.listens", "/data_dir_path", True, listeners
            )
        )

        self.assertEqual(conf["listeners"], listeners)

    def test_listeners_set_correctly_open_private_ports_true(self):
        listeners = [
            {
                "port": 8448,
                "resources": [{"names": ["federation"]}],
                "tls": True,
                "type": "http",
            },
            {
                "port": 443,
                "resources": [{"names": ["client"]}],
                "tls": False,
                "type": "http",
            },
            {
                "port": 1243,
                "resources": [{"names": ["client"]}],
                "tls": False,
                "type": "http",
                "bind_addresses": ["this_one_is_bound"],
            },
        ]

        expected_listeners = listeners.copy()
        expected_listeners[1]["bind_addresses"] = ["::1", "127.0.0.1"]

        conf = yaml.safe_load(
            ServerConfig().generate_config_section(
                "this.one.listens", "/data_dir_path", True, listeners
            )
        )

        self.assertEqual(conf["listeners"], expected_listeners)


class FederationBackoffTestCase(unittest.TestCase):
    """
    Tests for the "federation_backoff" settings dict.
    """

    def test_all_defaults(self):
        """
        When not defined, the defaults are all the Synapse standard ones.
        """
        config = {"server_name": "example.com"}
        t = ServerConfig()
        t.read_config(config, config_dir_path="", data_dir_path="")

        fb = t.server.federation_backoff_settings
        self.assertEqual(fb.dns_resolution, False)
        self.assertEqual(fb.dns_servfail, False)
        self.assertEqual(fb.no_route_to_host, False)
        self.assertEqual(fb.refused_connection, False)
        self.assertEqual(fb.cannot_assign_address, False)
        self.assertEqual(fb.invalid_tls, False)
        self.assertEqual(fb.on_timeout, False)
        self.assertEqual(fb.timeout_amount, 60000)

    def test_all_changed(self):
        """
        When defined, Synapse will take up the new settings.
        """
        config = {
            "server_name": "example.com",
            "federation_backoff": {
                "dns_resolution": True,
                "dns_servfail": True,
                "no_route_to_host": True,
                "refused_connection": True,
                "cannot_assign_address": True,
                "invalid_tls": True,
                "on_timeout": True,
                "timeout_amount": "30s",
            },
        }
        t = ServerConfig()
        t.read_config(config, config_dir_path="", data_dir_path="")

        fb = t.server.federation_backoff_settings
        self.assertEqual(fb.dns_resolution, True)
        self.assertEqual(fb.dns_servfail, True)
        self.assertEqual(fb.no_route_to_host, True)
        self.assertEqual(fb.refused_connection, True)
        self.assertEqual(fb.cannot_assign_address, True)
        self.assertEqual(fb.invalid_tls, True)
        self.assertEqual(fb.on_timeout, True)
        self.assertEqual(fb.timeout_amount, 30000)

    def test_timeout_amount_allowed_integer(self):
        """
        When federation_backoff.timeout_amount is given as an integer, it will
        be parsed as ms.
        """
        config = {
            "server_name": "example.com",
            "federation_backoff": {"timeout_amount": 30001},
        }
        t = ServerConfig()
        t.read_config(config, config_dir_path="", data_dir_path="")

        fb = t.server.federation_backoff_settings
        self.assertEqual(fb.timeout_amount, 30001)
