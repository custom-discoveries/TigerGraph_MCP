#********************************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# testSystemUtilities.py: This test case performs mock checks against the SystemUtilities class
#*********************************************************************************************

import unittest
from unittest.mock import MagicMock
from mcp_server.tigerGraph.services import TigerGraph_Session
from mcp_server.tigerGraph.system_services import SystemUtilities

class TestSystemUtilities(unittest.TestCase):

    def setUp(self):
        # Mock session and connection
        self.mock_session = MagicMock()
        self.mock_connection = MagicMock()

        self.mock_session.getConnection.return_value = self.mock_connection
        self.mock_session.getHost.return_value = "https://localhost"

        self.mock_response = {
            "ServiceStatusEvents": [
                {
                    "ServiceDescriptor": {"ServiceName": "GPE"},
                    "ServiceStatus": "Running",
                    "ProcessState": "Active"
                },
                {
                    "ServiceDescriptor": {"ServiceName": "GSQL"},
                    "ServiceStatus": "Stopped",
                    "ProcessState": "Inactive"
                }
            ]
        }

        self.mock_connection._post.return_value = self.mock_response
        self.system_util = SystemUtilities(self.mock_session)

    def test_displayServicesStatus_returns_expected_output(self):
        expected = [
            "GPE      Running  Active",
            "GSQL     Stopped Inactive"
        ]
        result = self.system_util.displayServicesStatus()
        self.assertEqual(result, expected)

    def test_displayServicesStatus_handles_exception(self):
        self.mock_connection._post.side_effect = Exception("Network error")
        result = self.system_util.displayServicesStatus()
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
