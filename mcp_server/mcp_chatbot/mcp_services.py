import os
import sys
import json
import asyncio
import traceback

from typing import List, Optional, Union

from mcp.shared.exceptions import McpError

from mcp import ClientSession, StdioServerParameters, ListToolsResult, Tool
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from contextlib import AsyncExitStack

from mcp_server.mcp_logger import setErrorHandler, logger
from mcp_server.config import getMCPServerConfig

MCP_FULL_PATH = getMCPServerConfig()

class MCPServices():

    def __init__(self, serverName:str):

        self.server_name =serverName
        self.tool_kit: dict[str, Tool] = {}
        self.tool_session: dict[str, ClientSession] = {}
        self.resource_session: dict[str, ClientSession] = {}
        self.tool_description = []
        self.prompt_description = []

        setErrorHandler()

    async def setToolList(self, session:ClientSession):

        try:        
            response:ListToolsResult = await session.list_tools()
            for tool in response.tools:
                self.tool_kit[tool.name] = tool
                self.tool_session[tool.name]  = session
                self.tool_description.append(
                    {
                        "server":self.server_name,
                        "name": tool.name,
                        "description": tool.description,
                        "required_params": tool.inputSchema.get("required",[]),
                        "properties":tool.inputSchema.get("properties",{})
                    }
                )

        except McpError as error:
            logger.warning(f"Looks like {self.server_name} Tools have not been installed - list_tools() {error}")

        except Exception as error:
            logger.error(f"Error in setToolList(): {error}")

    async def setPromptList(self, session:ClientSession):
        
        try:
            prompts_response = await session.list_prompts()
            if prompts_response and prompts_response.prompts:
                for prompt in prompts_response.prompts:
                    self.tool_kit[prompt.name] = prompt
                    self.tool_session[prompt.name] = session
                    self.prompt_description.append({
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": prompt.arguments
                    })
        except McpError as error:
            logger.warning(f"Looks like {self.server_name} Prompts have not been installed - list_prompts() {error}")

        except Exception as error:
            logger.error(f"Error in setPromptList(): {error}")

    async def setResourcesList(self, session:ClientSession):
        
        try:
            # List available resources
            resources_response = await session.list_resources()
            if resources_response and resources_response.resources:
                for resource in resources_response.resources:
                    resource_uri = str(resource.uri)
                    self.tool_kit[resource_uri] = resource
                    self.resource_session[resource_uri] = session


        except McpError as error:
            logger.warning(f"Looks like {self.server_name} Resources have not been installed - list_resources() {error}")

        except Exception as error:
            logger.error(f"Error in setResourcesList(): {error}")

    def getResourcesList(self) -> List:
        return self.resource_session.keys()

    async def callTool(self,toolName:str, arguments:dict):

        try:
            aSession = self.tool_kit.get(toolName)
            answer = await aSession.call_tool(toolName, arguments=arguments)
            return answer

        except Exception as error:
            print(f"Error in callTool(): {error}")

    def getPromptDescription(self) -> List:
        return self.prompt_description

    def getToolDescription(self) -> List:
        return self.tool_description
    
    def getToolSession(self,toolName:str) -> ClientSession:

        return self.tool_session.get(toolName,None)

    def getResourceSession(self,resourceName:str) -> ClientSession:

        return self.resource_session.get(resourceName,None)
    
    def getAllTools(self) -> List:
        toolList=[]

        for tool in self.tool_kit.values():
            if isinstance(tool,Tool):
                toolList.append(tool)

        return toolList

    def getToolsNames(self, formatted:Optional[bool]=False) -> Union[str, List[str]]:
        
        formatted_Tool_Names=""

        if not formatted:
            return self.tool_kit.keys()
        else:
            for toolName in self.tool_kit.keys():
                formatted_Tool_Names = f"{formatted_Tool_Names} {self.server_name}:{toolName}\n"

            return formatted_Tool_Names
        
        #self.formatted_tools:str = self.getToolNamesToString()

class MCPServer():

    def __init__(self):
    
        self.mcp_sessions:dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
    
    async def connect_to_servers(self):
        try:
            with open(f"{os.getcwd()}/{MCP_FULL_PATH}", "r") as file:
                data = json.load(file)
                servers = data.get("mcpServers", {})
                   
            for server_name, server_config in servers.items():
                    await self.initialize_mcp_servers(server_name, server_config)
            
        except Exception as e:
            logger.error(f"Error loading server config: {e}", file=sys.stderr)
            raise

    async def initialize_mcp_servers(self, server_name, server_config):

        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize the connection
            session.set_logging_level("critical")
            await session.initialize()
            self.mcp_sessions[server_name] = session

        except Exception as error:
            logger.error(f"Error in connect_to_mcp_server() {error}")    