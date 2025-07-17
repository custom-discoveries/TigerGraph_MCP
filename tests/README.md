# TigerGraph_MCP Unit Tests

This folder contains all the unit tests for TigerGraph_MCP.  

## Preparation

There is no TigerGraph configuration performed in the test scripts, all of your mcp_server/.env envronment varaibles needs to defined for a TigerGraph test server. (You will need to define your own Test Graph)

 - **testQueryRun** This is a mocked up version to run against the run_query service.
 
 - **exampleTestIntegrationQueryRun** This test case is a "live" test that connects to the TigerGraph database and allows you to define your own queries to test. You will need to copy the exampleTestIntegrationQueryRun to testIntegrationQueryRun.py (so as not to update the GitHub respository with your changes)

- **testPrettyPrintDirectory.py** This test case performs checks on the PrettyPrintDirectory class

- **testLiveSystemUtilities** This test case performs test against a live database on the SystemUtilities class

- **testSystemUtilities** This test case performs mock checks against the SystemUtilities class



