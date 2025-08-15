#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# mcp_chatbot.py: This modelue defines the Custom Discoveries  MCP ChatBot
#******************************************************************************
import asyncio
import warnings
import traceback

from typing import List, Optional
from autogen.events.agent_events import TextEvent
from mcp.shared.exceptions import McpError
from mcp_server.mcp_chatbot.mcp_services import MCPServer, MCPServices
from mcp_server.mcp_logger import setErrorHandler, logger, logging
from mcp_server.agents.ag2.chatAgent import ChatAgent

warnings.filterwarnings('ignore')
# Turn off specific library logging

logging.getLogger("Client").disabled = True
logging.getLogger("ag2").setLevel(logging.ERROR)
logging.getLogger('mcp.server.lowlevel.server').disabled = True

VERSION=3.1

class MCP_ChatBot:

    def __init__(self):

        self.mcpServices: dict[str, MCPServices] = {}

        # Hold mapping of resource name to resource url
        self.resourceURL={}

        setErrorHandler()
        # Initialize the client with your API key
            
    def getAgent(self) -> ChatAgent:
        return self.agent
    
    def setAgent(self,mcpServices:MCPServices):
        self.agent = ChatAgent(mcpServices)


    async def initialize_mcp_services(self, mcp_sessions:dict):
        try:

            for server_name, session in mcp_sessions.items():              
                mcpServices = MCPServices(server_name)
                self.mcpServices[server_name]=mcpServices
                                
                # List available tools
                await mcpServices.setToolList(session)

                # List available prompts
                await mcpServices.setPromptList(session)

                # List available resources
                await mcpServices.setResourcesList(session)

        except Exception as error:
            #traceback.print_exc()
            logger.error(f"Error in initialize_mcp_services({server_name}) {error}")
    
    async def process_query(self, query:str):

        try:
            
            await self.processAIAgent(query)

        except Exception as error:
            logger.error(f"Error in proess_query() {error}")

    async def processAIAgent(self, query="search for papers on knowledge graphs"):

        try:
            response = await self.getAgent().callMCPAgent(query)
            self.printResponse(response)

        except Exception as error:
            #traceback.print_exc()
            logger.error(f"Error in processAIAgent() {error}")

    def printResponse(self, response):
        if not isinstance(response,str):
            for event in response.events:
                if isinstance(event,TextEvent):
                    if event.content.recipient == "user":
                        event.print()
        else:
            print(response)


    def getToolNamesToString(self) -> str:
        formatted_tools="\n"
        total_tool_list:List = []
        #
        # Loop through all of the MCP Services (Servers) and 
        # get a complete list of all the tools that are connected
        #
        for mcp_services in self.mcpServices.values():
            total_tool_list.extend(mcp_services.getToolDescription())

        for i, tool in enumerate(total_tool_list):
            formatted_tools = f"{formatted_tools}{i+1}. {tool.get('server')}, {tool.get('name')}, valid_parameters:"
            if len(tool.get('properties')) == 0:
                formatted_tools = (f"{formatted_tools}None")
            else:
                for x, param in enumerate(tool.get('properties')):
                    comma = "," if x < (len(tool.get('properties'))-1) else ""
                    formatted_tools = (f"{formatted_tools} {param}{comma}")

                formatted_tools = f"{formatted_tools}, required_params:"
                for x, param in enumerate(tool.get('required_params')):
                    comma = "," if x < (len(tool.get('required_params'))-1) else ""
                    formatted_tools = (f"{formatted_tools} {param}{comma}")

            formatted_tools = f"{formatted_tools}\n"


        return formatted_tools


    def getAllTools(self,server_name:Optional[str]="") -> List[str]:
        
        total_tool_list:List = []
        #
        # Loop through all of the MCP Services (Servers) and 
        # get a complete list of all the tool descriptions
        #
        if server_name == "":
            for mcp_services in self.getAgent().getMCPServices().values():
                total_tool_list.extend(mcp_services.getToolDescription())
        
            return total_tool_list
        else: 
        #
        # Lookup MCP Services by name and return the 
        # tool descriptions for that service
        #            
            mcp_services:MCPServices = self.getAgent().getMCPServices().get(server_name,"")
            if mcp_services:
                return mcp_services.getToolDescription()
            else:
                print(f"No Services found for: {server_name}")

    def getAllPrompts(self,server_name:Optional[str]="") -> List[str]:
        
        total_prompt_list:List = []
        #
        # Loop through all of the MCP Services (Servers) and 
        # get a complete list of all the prompt descriptions
        #
        if server_name == "":
            for mcp_services in self.mcpServices.values():
                total_prompt_list.extend(mcp_services.getPromptDescription())
        
            return total_prompt_list
        else: 
        #
        # Lookup MCP Services by name and return the 
        # tool descriptions for that service
        #            
            mcp_services:MCPServices = self.mcpServices.get(server_name,"")
            if mcp_services:
                return mcp_services.getPromptDescription()
            else:
                print(f"No Services found for: {server_name}")

    def getAllResources(self,url_name:Optional[str]="") -> List[str]:
        
        total_resources_list:List = []
        #
        # Loop through all of the MCP Services (Servers) and 
        # get a complete list of all the resources descriptions
        #
        if url_name == "":
            for mcp_services in self.mcpServices.values():
                total_resources_list.extend(mcp_services.getResourcesList())
        
            return total_resources_list
        else: 
        #
        # Lookup MCP Services by name and return the 
        # tool descriptions for that service
        #            
            for mcp_services in self.mcpServices.values():
                session = mcp_services.getResourceSession(url_name)
                if session is not None:
                    return session
            
            if session is None:
                print(f"No MCP Resources found for: {url_name}")

    async def get_resource(self, resource_uri, session):
        
        if not session:
            print(f"Resource '{resource_uri}' not found.")
            return
        
        try:      
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available.")
        except McpError as error:
            print(f"MCP Session Read Error: {error}")
        except Exception as e:
            print(f"Error: {e}")

    async def list_tools(self,server_name:Optional[str]=""):
        """List all available tools."""

        listOfTools = self.getAllTools(server_name)
        if not listOfTools:
            print("No Tools available.")
            return
        
        print("\nAvailable Tools:")
        header = None
        for tool in listOfTools:

            if header != tool['server']:
                print(f"Server: {tool['server']}\n")
                print(f" - Name: {tool['name']}\n - Required Parameters: {tool.get("required_params")}\n - Description: {tool['description']}\n")
            else:
                print(f" - Name: {tool['name']}\n - Required Parameters: {tool.get("required_params")}\n - Description: {tool['description']}\n")

            header = tool['server']    

    async def list_prompts(self,server_name:Optional[str]=""):
        """List all available prompts."""
        listOfPrompts = self.getAllPrompts(server_name)
        if not listOfPrompts:
            print("No prompts available.")
            return
        
        print("\nAvailable prompts:")
        for prompt in listOfPrompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"  Arguments:")
                for arg in prompt['arguments']:
                    arg_name = arg.name if hasattr(arg, 'name') else arg.get('name', '')
                    print(f"    - {arg_name}")
    
    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return
        
        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content
                
                # Extract text from content (handles different formats)
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, 'text'):
                    text = prompt_content.text
                else:
                    # Handle list of content items
                    text = " ".join(item.text if hasattr(item, 'text') else str(item) 
                                  for item in prompt_content)
                
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    async def chat_loop(self):

        print(f"\n\nWelcome to Custom Discoveries MCP Chatbot {VERSION}\n")
        print("\nType your queries or type ['quit'|'exit'] to exit.")   
        self.printChatMenu()            

        self.setAgent(self.mcpServices)
        self.initializeResourceNames()

        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue
        
                if (query.lower() == 'quit') or (query.lower() == 'exit'):
                    break
                
                # Check for @resource syntax first
                if query.startswith('@'):
                    # Remove @ sign  
                    resource_uri=""
                    temp_query = query[1:]
                    query_array = temp_query.split(" ")
                    index = len(query_array)
                    query_name = query_array[0]
                    resource_uri:str = self.resourceURL.get(query_name)
                    session = self.getAllResources(resource_uri)
                    if resource_uri is not None:
                        if (index > 1):
                            uriIndex = resource_uri.find("//")
                            resource_uri = f"{resource_uri[:uriIndex+2]}{query_array[1]}"
                        await self.get_resource(resource_uri, session, )
                    else:
                        logger.warning(f"No Resource {query_name} Found!")
                    continue
                
                # Check for /command syntax
                if query.startswith('/'):
                    parts = query.split()
                    command = parts[0].lower()

                    if command == '/help':
                        self.printChatMenu()

                    elif command == '/tools':
                        if len(parts) > 1:
                            await self.list_tools(parts[1])
                        else:
                            await self.list_tools()
 
                    elif command == '/prompts':
                        await self.list_prompts()
 
                    elif command == '/resources':

                        print("\nList of Resources:")
                        for item in self.resourceURL:
                            print(f"  @{item} [folder name]")

                    elif command == '/prompt':
                        if len(parts) < 2:
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                            continue
                        
                        prompt_name = parts[1]
                        args = {}
                        
                        # Parse arguments
                        for arg in parts[2:]:
                            if '=' in arg:
                                key, value = arg.split('=', 1)
                                args[key] = value
                        
                        await self.execute_prompt(prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                    continue
                
                await self.process_query(query)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")

    def printChatMenu(self):
 
        print("\nUse /tools | /tools tigerGraph to list available tools of MCP server")
        print("Use /prompts to list available prompts")
        print("Use /resources to list available resources")
        print("Use /help to reprint this menu")
        print("\nUse @listOutput to see available TigerGraph Query Output Files")
        print("Use @listOutput <query_file_name> list content of TigerGraph Query Output file")

    def initializeResourceNames(self):
        resources = self.getAllResources()
        for item in resources:
            index = item.find("//")
            self.resourceURL[item[index+2:]]=item
    
    async def cleanup(self, mcpServer:MCPServer):
        await mcpServer.exit_stack.aclose()

    async def main(self):

        mcpServer = MCPServer()

        try:
            await mcpServer.connect_to_servers()
            await self.initialize_mcp_services(mcpServer.mcp_sessions)
            await self.chat_loop()
        finally:
            await self.cleanup(mcpServer)


if __name__ == "__main__":

    chatbot = MCP_ChatBot()
    asyncio.run(chatbot.main())