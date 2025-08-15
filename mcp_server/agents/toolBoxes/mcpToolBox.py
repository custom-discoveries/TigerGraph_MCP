#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# mcpToolBox.py: Holds all the "Tools"/"Functions" used by the Agents
#******************************************************************************

from typing import Annotated, List

from autogen.agentchat.group import (ReplyResult,
                                     ContextVariables
                                     )


def record_mcp_params(       
    request: Annotated[List, "LLM Resonse"],
    context: ContextVariables
) -> ReplyResult: 
    """
    Analyze a user request to determine MCP server and tool to use
    """
    #print(f"record_mcp_params request = {request}")
    reqDict:dict = request.pop()

    server_name = reqDict.get("server_type")
    tool_name = reqDict.get("tool_type")
    attributes = reqDict.get("required_params")
    context["server_name"] = server_name
    context["tool_name"] = tool_name
    context["attributes"] = attributes
    context["completed_stage"] = "RECORD_MCP_PARAMS"
      
    return ReplyResult(
        message=f"Pass back the results: {server_name}, {tool_name}, {attributes}",
        context_variables=context
    )
