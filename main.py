#******************************************************************************
# Copyright (c) 2025, Custom Discoveries Inc.
# All rights reserved.
# main.py: This modelue invokes the TigerGraph MCP Server 
#******************************************************************************
from mcp_server.tigerGraph.MCP_Server import TigerGraph_MCP_Server

# launch the MCP app
if __name__ == "__main__":
    server = TigerGraph_MCP_Server()
    server.run_server()
