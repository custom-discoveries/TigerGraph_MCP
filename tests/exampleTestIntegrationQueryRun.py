#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
#
# exampleTestIntegrationQueryRun.py: This test case is a "live" test that 
# connects to the TigerGraph database and allows you to define your own 
# queries to test. You will need to copy the exampleTestIntegrationQueryRun 
# to testIntegrationQueryRun.py (so as not to update the GitHub respository 
# with your changes)
#******************************************************************************

import unittest
import json
import os
import time
from unittest import skip
from mcp_server.config import tigerGraphConstants
from mcp_server.tigerGraph.services import TigerGraphServices
from mcp_server.mcp_logger import setErrorHandler, logger

HOST, GRAPH, USER, PASSWORD, SECRET, TOKEN = tigerGraphConstants()


class TestRunQueryIntegration(unittest.TestCase):
    """Integration tests for run_query method with real database connections.
    
    These tests require:
    - A running TigerGraph database instance
    - Valid connection credentials
    - Test queries installed on the database
    """
    OUTPUT_PATH = tigerGraphConstants(output=True)
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        
        # Initialize the class instance with real database connection
        setErrorHandler()
        cls.OUTPUT_PATH = tigerGraphConstants(output=True)
        cls.db_instance = TigerGraphServices()
        
        # Test query names that should exist in your database
        cls.test_queries = {
            'simple_query': 'your_simple_query',
            'parameterized_query': 'your_parameterized_query',
            'empty_result_query': 'your_empy_results_query'
        }
        
        # Create temporary directory for output files
        cls.temp_dir = cls.OUTPUT_PATH #tempfile.mkdtemp()
        
        # Verify database connection
        try:
            connection = cls.db_instance.getConnection()
            if not connection:
                raise unittest.SkipTest("Could not establish database connection")
        except Exception as e:
            raise unittest.SkipTest(f"Database connection failed: {str(e)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are complete."""
        # Clean up temporary files
        #import shutil
        # if os.path.exists(cls.temp_dir):
        #     shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up before each test method."""
        # Update OUTPUT_PATH to use temporary directory
        self.original_output_path = self.OUTPUT_PATH
        self.OUTPUT_PATH = self.temp_dir
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original OUTPUT_PATH
        if hasattr(self, 'original_output_path'):
            self.OUTPUT_PATH = self.original_output_path
        
        # Clean up any test files created
        # for file in os.listdir(self.temp_dir):
        #     file_path = os.path.join(self.temp_dir, file)
        #     if os.path.isfile(file_path):
        #         os.remove(file_path)
    
    def test_run_query_returns_terminal_format_with_real_data(self):
        """Test run_query returns formatted JSON with real database data."""
        # Arrange
        query_name = self.test_queries['parameterized_query']
        params = {
            "your_parameter": "your_value"
        }
        
        # Act
        result = self.db_instance.run_query(
            query_name=query_name,
            params=params,
            timeout=30,
            outputFormat='terminal'
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # Verify it's valid JSON
        try:
            parsed_result = json.loads(result)
            self.assertIsInstance(parsed_result, (dict, list))
        except json.JSONDecodeError:
            self.fail("Result is not valid JSON")
        
        # Verify the formatting matches expected pattern
        self.assertIn(',', result)  # Custom separator should be present
        self.assertIn(':', result)  # Custom separator should be present
    
    def test_run_query_creates_csv_file_with_real_data(self):
        """Test run_query creates CSV file with real database results."""
        # Arrange
        query_name = self.test_queries['parameterized_query']
        params = {
            "your_parameter": "your_value"
        }
        expected_csv_path = os.path.join(self.temp_dir, f"{query_name}.csv")
        
        # Act
        result = self.db_instance.run_query(
            query_name=query_name,
            params=params,
            timeout=30,
            outputFormat="csv"
        )
        
        # Assert
        self.assertIn("Writing",result)  # Method should not return data for CSV output
        self.assertTrue(os.path.exists(expected_csv_path), 
                       f"CSV file was not created at {expected_csv_path}")
        
        # Verify file has content
        with open(expected_csv_path, 'r', encoding='utf-8') as file:
            content = file.read()
            self.assertGreater(len(content), 0, "CSV file is empty")
            
        # Verify file size is reasonable (not just headers)
        file_size = os.path.getsize(expected_csv_path)
        self.assertGreater(file_size, 10, "CSV file appears to contain no data")
    
    def test_run_query_creates_json_file_with_real_data(self):
        """Test run_query creates JSON file with real database results."""
        # Arrange
        query_name = self.test_queries['parameterized_query']
        params = {
            "award_id": "211883"
        }
        expected_json_path = os.path.join(self.temp_dir, f"{query_name}.json")
        
        # Act
        result = self.db_instance.run_query(
            query_name=query_name,
            params=params,
            outputFormat="json",
            timeout=30
        )
        
        # Assert
        self.assertIn("Writing",result)  # Method should not return data for JSON output
        self.assertTrue(os.path.exists(expected_json_path), 
                       f"JSON file was not created at {expected_json_path}")
        
        # Verify file contains valid JSON
        with open(expected_json_path, 'r', encoding='utf-8') as file:
            try:
                json_data = json.load(file)
                self.assertIsInstance(json_data, (dict, list))
            except json.JSONDecodeError:
                self.fail("Created JSON file contains invalid JSON")
        
        # Verify file has reasonable content
        file_size = os.path.getsize(expected_json_path)
        self.assertGreater(file_size, 20, "JSON file appears to be empty or minimal")
    
    def test_run_query_with_parameterized_query(self):
        """Test run_query works correctly with query parameters."""
        # Arrange
        query_name = self.test_queries['parameterized_query']
        params = {
            "your_parameter": "your_value",
        }
        
        # Act
        result = self.db_instance.run_query(
            query_name=query_name,
            params=params,
            timeout=30
        )
        
        # Assert
        self.assertIsNotNone(result)
        
        # Verify the query executed (even if no results found)
        self.assertIsInstance(self.db_instance.emptyResults, bool)
    
    def test_run_query_handles_empty_results_from_database(self):
        """Test run_query correctly handles queries that return no results."""
        # Arrange
        query_name = self.test_queries['empty_result_query']
        params = {}
        
        # Act
        result = self.db_instance.run_query(
            query_name=query_name,
            params=params,
            timeout=30,
            outputFormat="json"
        )
        
        # Assert
        #self.assertIsNone(result)
        self.assertEqual(result,"")
        self.assertTrue(self.db_instance.emptyResults, 
                       "Empty results should be detected correctly")
    
    def test_run_query_respects_timeout_parameter(self):
        """Test run_query respects the timeout parameter."""
        # Arrange
        query_name = self.test_queries['simple_query']
        short_timeout = 1  # 1 second timeout
        
        # Act & Assert
        start_time = time.time()
        try:
            self.db_instance.run_query(
                query_name=query_name,
                params={},
                timeout=short_timeout
            )
            execution_time = time.time() - start_time
            
            # If query completes quickly, that's fine
            # If it takes longer than expected, it should have timed out
            if execution_time > (short_timeout + 5):  # 5 second buffer
                self.fail("Query did not respect timeout parameter")
                
        except Exception as e:
            # Timeout exceptions are expected for long-running queries
            execution_time = time.time() - start_time
            self.assertLessEqual(execution_time, short_timeout + 10, 
                               "Timeout occurred but took too long")
    
    def test_run_query_database_connection_persistence(self):
        """Test that multiple queries can be run with the same connection."""
        # Arrange
        query_name = self.test_queries['simple_query']
        
        # Act - Run multiple queries
        result1 = self.db_instance.run_query(
            query_name=query_name,
            timeout=30,
            outputFormat="terminal"
        )
        
        result2 = self.db_instance.run_query(
            query_name=query_name,
            timeout=30,
            outputFormat="terminal"
        )
        
        # Assert
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        # Results should be consistent for the same query
        self.assertEqual(result1, result2)
    
    @skip("Only run for performance testing")
    def test_run_query_performance_benchmark(self):
        """Benchmark test for query performance - skip by default."""
        # Arrange
        query_name = self.test_queries['simple_query']
        max_acceptable_time = 10.0  # seconds
        
        # Act
        start_time = time.time()
        result = self.db_instance.run_query(
            query_name=query_name,
            timeout=60,
            outputFormat="terminal"            
        )
        execution_time = time.time() - start_time
        
        # Assert
        self.assertIsNotNone(result)
        self.assertLess(execution_time, max_acceptable_time,
                       f"Query took {execution_time:.2f}s, expected < {max_acceptable_time}s")
        
        print(f"Query execution time: {execution_time:.2f} seconds")
    
    def runSingleTest(unit_test_name:str):
        suite = unittest.TestSuite()
        suite.addTest(TestRunQueryIntegration(unit_test_name))
        # Run the specific test
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)

if __name__ == '__main__':
    # Run with environment variable to control test execution
    if os.getenv('RUN_INTEGRATION_TESTS', 'false').lower() == 'true':
        
        #runSingleTest('test_run_query_creates_json_file_with_real_data')
        unittest.main(verbosity=2)       
    else:
        logger.info("Integration tests skipped. Set RUN_INTEGRATION_TESTS=true to run.")
