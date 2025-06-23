#******************************************************************************
# Copyright (c) 2025, Custom Discoveries Inc.
# All rights reserved.
# main.py: This modelue invokes the TigerGraph MCP Server 
#******************************************************************************
import asyncio
import warnings

# Suppress all logs below WARNING globally 
warnings.filterwarnings('ignore')

from mcp_server.mcp_chatbot.mcp_chatbot import MCP_ChatBot

# launch the MCP app
if __name__ == "__main__":
    chatbot = MCP_ChatBot()
    asyncio.run(chatbot.main())

