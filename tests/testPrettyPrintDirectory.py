#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# testPrettyPrintDireectory.py: This test case performs checks on the 
# PrettyPrintDirectory class
#******************************************************************************

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from mcp_server.tigerGraph.prettyPrintDir import PrettyPrintDirectory
from mcp_server.mcp_logger import setErrorHandler, logger, logging

class TestPrettyPrintDirectory(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and add test files
        setErrorHandler()
        self.test_dir = tempfile.mkdtemp()
        self.test_file_1 = Path(self.test_dir) / "file1.txt"
        self.test_file_2 = Path(self.test_dir) / "file2.log"

        self.test_file_1.write_text("This is a test file.")
        self.test_file_2.write_bytes(b"\x00\x01\x02\x03")

        self.printer = PrettyPrintDirectory(self.test_dir)

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_get_formated_file_dir_returns_list(self):
        output = self.printer.getFormatedFileDir()
        self.assertIsInstance(output, list)
        self.assertTrue(any("file1.txt" in line for line in output))
        self.assertTrue(any("file2.log" in line for line in output))
        self.assertTrue(any("Total files" in line for line in output))
        self.assertTrue(any("Total size" in line for line in output))

    def test_get_file_info_valid_file(self):
        info = self.printer.get_file_info(self.test_file_1)
        self.assertIn('name', info)
        self.assertIn('size_bytes', info)
        self.assertIn('modified', info)
        self.assertEqual(info['name'], 'file1.txt')
        self.assertTrue(info['size_bytes'] > 0)

    def test_get_file_info_handles_directory(self):
        info = self.printer.get_file_info(Path(self.test_dir))
        self.assertEqual(info, {})  # Should return empty dict for directory

    def test_format_file_size(self):
        self.assertEqual(self.printer.format_file_size(0), "0 B")
        self.assertEqual(self.printer.format_file_size(512), "512.00 B")
        self.assertEqual(self.printer.format_file_size(2048), "2.00 KB")
        self.assertEqual(self.printer.format_file_size(1024 ** 2), "1.00 MB")

    def test_get_list_files(self):
        files = self.printer.get_list_files(Path(self.test_dir))
        if logger.level == logging.DEBUG:
            logger.debug(files)
        self.assertEqual(len(files), 2)
        self.assertTrue(all(isinstance(f, Path) for f in files))

    def test_get_formated_file_dir_permission_error(self):
        # Simulate permission error by pointing to non-existent folder (assuming restricted)
        restricted_path = "/root/restricted_dir"
        printer = PrettyPrintDirectory(restricted_path)
        output = printer.getFormatedFileDir()
        self.assertEqual(output, [])

if __name__ == '__main__':
    unittest.main()