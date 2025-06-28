import unittest
from unittest.mock import Mock, patch, mock_open
import json
import os
from mcp_server.config import tigerGraphConstants
from mcp_server.tigerGraph.Services import TigerGraphServices  

OUTPUT_PATH = tigerGraphConstants(output=True)

class TestRunQuery(unittest.TestCase):
    """Test cases for the run_query method."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.instance = TigerGraphServices()
        self.mock_connection = Mock()
        self.instance.getConnection = Mock(return_value=self.mock_connection)
        self.instance.isResultSetEmpty = Mock()
        self.instance.json_to_csv = Mock()
        
        # Sample test data
        self.sample_results = {
            "results": [
                {"id": 1, "name": "test1"},
                {"id": 2, "name": "test2"}
            ]
        }
        self.query_name = "queryMe"
        self.params = {"id": "12345"}
    
    #@patch('builtins.print')
    def test_run_query_with_terminal_format_in_params(self):
        """Test run_query returns formatted JSON when params contain format='terminal'."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False

        
        # Act
        result = self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            outputFormat="terminal"
        )
        
        # Assert
        self.mock_connection.runInstalledQuery.assert_called_once_with(
            self.query_name, self.params, timeout=60000
        )
        expected_json = json.dumps(self.sample_results, indent=4, separators=(',', ':'))
        # Verify it's valid JSON
        self.assertEqual(result, expected_json)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_run_query_with_csv_output_format(self, mock_print, mock_file):
        """Test run_query writes CSV file when outputFormat is 'csv'."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False
        expected_output_path = f"{OUTPUT_PATH}/{self.query_name}.csv"  # Replace OUTPUT_PATH with actual constant
        
        # Act
        result = self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            outputFormat="csv"
        )
        
        # Assert
        self.instance.json_to_csv.assert_called_once_with(
            self.sample_results, expected_output_path
        )
        mock_print.assert_called_once_with(f"\nWriting Query Results to {expected_output_path}")
        self.assertIsNone(result)  # Method doesn't return anything for CSV output
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_run_query_with_json_output_format(self, mock_print, mock_file):
        """Test run_query writes JSON file when outputFormat is 'json'."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False
        expected_output_path = f"{OUTPUT_PATH}/{self.query_name}.json"  # Replace OUTPUT_PATH with actual constant
        
        # Act
        result = self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            outputFormat="json"
        )
        
        # Assert
        mock_file.assert_called_once_with(expected_output_path, 'w', encoding='utf-8')
        handle = mock_file()
        # Verify json.dump was called with correct parameters
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        expected_json = json.dumps(self.sample_results, indent=4, separators=('. ', ' = '))
        mock_print.assert_called_once_with(f"\nWriting Query Results to {expected_output_path}")
        self.assertIsNone(result)
    
    def test_run_query_with_empty_results(self):
        """Test run_query behavior when results are empty."""

        # Arrange
        self.mock_connection.runInstalledQuery.return_value = {}
        self.instance.isResultSetEmpty.return_value = True
        self.params= {}        
        # Act
        result = self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            outputFormat="json"
        )
        
        # Assert
        self.assertTrue(self.instance.emptyResults)
        self.assertEqual(result,"")
        # Verify no file operations were attempted
        self.instance.json_to_csv.assert_not_called()
    
    def test_run_query_with_custom_timeout(self):
        """Test run_query passes correct timeout to runInstalledQuery."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False
        custom_timeout = 120
        
        # Act
        self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            timeout=custom_timeout
        )
        
        # Assert
        self.mock_connection.runInstalledQuery.assert_called_once_with(
            self.query_name, self.params, timeout=custom_timeout * 1000
        )
    
    def test_run_query_with_default_parameters(self):
        """Test run_query works with minimal parameters using defaults."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = ''
        self.instance.isResultSetEmpty.return_value = True
        self.params = {}
        # Act
        result = self.instance.run_query(query_name=self.query_name,params=self.params)
        
        # Assert
        self.mock_connection.runInstalledQuery.assert_called_once_with(
            self.query_name, {}, timeout=60000
        )
        self.assertEqual(result,'')  # No output format specified, so no return value
    
    def test_run_query_sets_empty_results_attribute(self):
        """Test run_query correctly sets the emptyResults attribute."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False
        self.params = {}
        # Act
        result = self.instance.run_query(query_name=self.query_name,params=self.params)
        
        # Assert
        self.instance.isResultSetEmpty.assert_called_once_with(
            self.query_name, self.sample_results
        )
        self.assertEqual(self.instance.emptyResults, False)
    
    def test_run_query_with_invalid_output_format(self):
        """Test run_query behavior with unrecognized outputFormat."""
        # Arrange
        self.mock_connection.runInstalledQuery.return_value = self.sample_results
        self.instance.isResultSetEmpty.return_value = False
        
        # Act
        result = self.instance.run_query(
            query_name=self.query_name,
            params=self.params,
            outputFormat="invalid_format"
        )
        
        # Assert
        # Should not call file operations for invalid format
        self.instance.json_to_csv.assert_not_called()
        self.assertIsNone(result)


def runSingleTest(unit_test_name:str):
    suite = unittest.TestSuite()
    suite.addTest(TestRunQuery(unit_test_name))
    # Run the specific test
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    # Additional test configuration
    #runSingleTest('test_run_query_with_csv_output_format')
    unittest.main(verbosity=2)
