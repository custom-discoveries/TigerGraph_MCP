#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# toolKitPrompt.py: Holds all the prompts used by the Agents
#******************************************************************************

processing_prompt="""Your are a Model Context Protocal (MCP) Expert. You need
to figure out which MCP tool to use from the users query: {query}. You will 
need to lookup the MCP Server tool to use from the users input. From the tool,
you need to identify which MCP server the tool belongs to. Here are the names
of the servers and the tools that are associated with that server:{listOfTools}

Instructions:
Return a JSON array with the following format:
[{{
'server_type':server_name,
'tool_type':tool_name,
'required_params':{{par1:value, par2:value, par3:value}}
}}]
use the record_mcp_params tool to capture your response consistently and 
log it for future reference. The output must consist solely of the valid 
JSON array. Do not include any preceding or trailing text, markdown code 
block delimiters (e.g., ```json), or comments. Each element within this 
array must be a JSON object. If you cannot resolve which tool name, then 
put in 'unknown' as tool type. You will need to determine if the tool has any 
required parameters and identify the parameter name. If the tool doesn't have any
required parameters, then set 'required_params' to 'None'."""

pretty_print_prompt= """Format a given list of strings into a neatly sorted table 
or a bullet-point list. Optionally, enhance the chosen format with appropriate icons. 
NOTE: The entire output must be returned as a single string, not as a data structure 
like a dictionary or array."""
