#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# main.py: This modelue invokes the TigerGraph MCP Server 
#******************************************************************************
import os
from mcp_server.tigerGraph.mcp_Server import TigerGraph_MCP_Server

# launch the MCP app
if __name__ == "__main__":
    print(f"Running from: {os.getcwd()}")
    server = TigerGraph_MCP_Server()
    server.run_server()
