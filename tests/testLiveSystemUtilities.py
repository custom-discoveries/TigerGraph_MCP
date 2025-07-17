import unittest
import logging

from unittest.mock import MagicMock
from mcp_server.tigerGraph.services import TigerGraph_Session
from mcp_server.tigerGraph.system_services import SystemUtilities
from mcp_server.mcp_logger import setErrorHandler, logger


class TestSystemUtilities(unittest.TestCase):

    def setUp(self):
        setErrorHandler()
        # Mock session and connection
        self.session = TigerGraph_Session()
        self.connection = self.session.getConnection()

        self.system_util = SystemUtilities(self.session)

    def test_displayAllJobs_returns_expected_output(self):

        result = self.system_util.displayAllJobs()
        logger.debug(result)
        self.assertEqual(len(result), 2)

    def test_displayCPUMemoryStatus_returns_expected_output(self):

        result = self.system_util.displayCPUMemoryStatus()
        self.assertEqual(len(result), 19)

    def test_displayDiskStatus_returns_expected_output(self):

        result = self.system_util.displayDiskStatus()
        self.assertEqual(len(result), 16)

    def test_displayComponentVersion_returns_expected_output(self):

        result = self.system_util.displayComponentVersion()
        if logger.level == logging.DEBUG:
            for item in result: print(f"{item}")
            print(f"\n")

        self.assertEqual(len(result), 12)

    def test_displayServicesStatus_returns_expected_output(self):
        result = self.system_util.displayServicesStatus()
        self.assertEqual(len(result), 16)

    def test_displayDetailedServicesStatus_returns_expected_output(self):
        result = self.system_util.displayDetailedServicesStatus()
        self.assertEqual(len(result), 47)

if __name__ == '__main__':
    unittest.main()
