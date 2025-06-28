#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# mcp_chatbot.py: This modelue defines the Custom Discoveries  MCP ChatBot
#******************************************************************************
import json
import asyncio
import sys
import os
import warnings

from typing import List
from anthropic import Anthropic
from anthropic.types import MessageParam
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph
from langchain_community.agent_toolkits.load_tools import load_tools, get_all_tool_names
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from mcp_server.config import initialLLMConstants

warnings.filterwarnings('ignore')

API_KEY, LLM_MODEL, TOKENS, LLM_MODEL_FAMILY, ANTHROPIC, OPENAI = initialLLMConstants()

class MCP_ChatBot:

    def __init__(self):
        
        # Initialize the client with your API key
        if LLM_MODEL_FAMILY == ANTHROPIC:
            self.anthropic = Anthropic(
                api_key=API_KEY  # Get this from console.anthropic.com
            )

        elif  LLM_MODEL_FAMILY == OPENAI:
            self.openAI = OpenAI(
                api_key=API_KEY
            )

        self.exit_stack = AsyncExitStack()
        # Tools list required for Anthropic API
        self.available_tools = []
        # Prompts list for quick display 
        self.available_prompts = []
        # Sessions dict maps tool/prompt names or resource URIs to MCP client sessions
        self.sessions = {}
    
    def getAgent(self) -> CompiledGraph:
        return self.agent
    
    def setAgent(self,agent:CompiledGraph):
        self.agent = agent

    def getTokens(self) -> int:
        return TOKENS

    def getModel(self):
        return LLM_MODEL

    async def initialize_langChain_agent(self, tools):
        ChatAgent(self,tools)
        #self.agent.get_graph().draw_mermaid_png(output_file_path="./ai_graph_output.png")

    async def connect_to_mcp_server(self, server_name, server_config):
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
            await session.initialize()
            
            try:
                # List available tools
                response = await session.list_tools()
                if LLM_MODEL_FAMILY == ANTHROPIC:
                    for tool in response.tools:
                        self.sessions[tool.name] = session
                        self.available_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        })
                elif LLM_MODEL_FAMILY == OPENAI:
                    tools = await load_mcp_tools(session)
                    for tool in tools:
                        self.available_tools.append( {
                                        "type": "function",
                                        "function": { "name":tool.name,
                                        "description":tool.description,
                                        "properties": {"type": tool.tool_call_schema["properties"]} 
                                        }
                    })                       
                    await self.initialize_langChain_agent(tools)
                else:
                    raise ProcessLookupError("Error in connect_to_mcp_server(), no valid LLM_MODEL_FAMILY specified!")

                # List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append({
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": prompt.arguments
                        })
                # List available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        resource_uri = str(resource.uri)
                        self.sessions[resource_uri] = session
            
            except Exception as e:
                print(f"Error {e}", file=sys.stderr)
                
        except Exception as e:
            print(f"Error connecting to {server_name}: {e}")

    async def connect_to_servers(self):
        try:
            with open(f"{os.getcwd()}/mcp_server/mcp_chatbot/server_config.json", "r") as file:
                data = json.load(file)
                servers = data.get("tigerGraph_MCP_Server", {})
                   
            for server_name, server_config in servers.items():
                    await self.connect_to_mcp_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server config: {e}", file=sys.stderr)
            raise
    
    async def process_query(self, query:str):


        messages: List[MessageParam] = [{'role': 'user', 'content': query}]

        try:
            if  LLM_MODEL_FAMILY == OPENAI:
                await self.processAIAgent(query)

            elif LLM_MODEL_FAMILY == ANTHROPIC:
                await self.processAnthropicAIQuery(messages)

        except Exception as error:
            print(f"Error in proess_query() {error}")

    async def processAIAgent(self, query):
        prompt = f""" 1. Take all the necessary steps, using the the tools passed in to answer the request.
                      2. Take the output query and please convert it into a clear, human-readable summary 
                      using bullet points or formatted sections where appropriate.
                      {query}
                      """

        response = await self.agent.ainvoke({"messages": prompt})
        answer = response['messages'][len(response['messages'])-1].content
        #print(f"Number of steps executed: {len(response['messages'])}\n")
        print(answer)

    async def processAnthropicAIQuery(self, messages):
        response=""
        response_content=""

        while True:
            try:
                response = self.anthropic.messages.create(
                                max_tokens = self.getTokens(),
                                model = self.getModel(), 
                                tools = self.available_tools,
                                messages = messages
                            )

                has_tool_use = False
                assistant_content = []

                response_content = response.content
                for content in response_content:
                    if content.type == 'text':
                        print(content.text)
                        assistant_content.append(content)
                    elif content.type == 'tool_use':
                        has_tool_use = True
                        assistant_content.append(content)
                        messages.append({'role':'assistant', 'content':assistant_content})
                        
                        # Get session and call tool
                        session = self.sessions.get(content.name)
                        if not session:
                            print(f"Tool '{content.name}' not found.")
                            break
                            
                        result = await session.call_tool(content.name, arguments=content.input)
                        messages.append({
                            "role": "user", 
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content
                                }
                            ]
                        })
                # Exit loop if no tool was used
                if not has_tool_use:
                    break
            except Exception as error:
                raise ProcessLookupError(f"Error in processOpenAiQuery(): {error}")
        
        return response

    async def get_resource(self, resource_uri):
        session = self.sessions.get(resource_uri)
        
        # Fallback for papers URIs - try any papers resource session
        if not session and resource_uri.startswith("querydir://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("querydir://"):
                    session = sess
                    break
            
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
        except Exception as e:
            print(f"Error: {e}")

    async def list_tools(self):
        """List all available prompts."""
        if not self.available_tools:
            print("No Tools available.")
            return
        
        print("\nAvailable Tools:")
        for tool in self.available_tools:
            if LLM_MODEL_FAMILY == ANTHROPIC:
                print(f"- {tool['name']}: {tool['description']}")
            else:  
                print(f"- {tool['function']['name']}: {tool['function']['description']}")

    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return
        
        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
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
            print(f"Error: {e}")
    
    async def chat_loop(self):
        print("\nWelcome to Custom Discoveries TigerGraph MCP Chatbot!\n")
        print("Type your queries or type ['quit'|'exit'] to exit.")    
        print("Use @listQueries to see available Query Output Files")
        print("Use @<query_file_name> list content of Query file")            
        print("Use /tools to list available tools")
        print("Use /prompts to list available prompts")
        
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
                    query_file_name = query[1:]
                    if query_file_name == "listQueries":
                        resource_uri = "querydir://listQueries"
                    else:
                        resource_uri = f"querydir://{query_file_name}"
                    await self.get_resource(resource_uri)
                    continue
                
                # Check for /command syntax
                if query.startswith('/'):
                    parts = query.split()
                    command = parts[0].lower()
                    if command == '/tools':
                        await self.list_tools()
                    elif command == '/prompts':
                        await self.list_prompts()
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
    
    async def cleanup(self):
        await self.exit_stack.aclose()

    async def main(self):

        try:
            await self.connect_to_servers()
            await self.chat_loop()
        finally:
            await self.cleanup()

class ChatAgent:
    """
    ChatAgent class is used to support langchain Agent based soltuion

    """
    def __init__(self, client:MCP_ChatBot, tools:List):
        self.agent = create_react_agent(self.getLLMModel(), tools)
        client.setAgent(self.agent)

    def getLLMModel(self):
        return(ChatOpenAI(temperature=0, model=LLM_MODEL))
        
    def list_BuiltIn_tools(self):
        return print(f"List of Tools: {json.dumps(get_all_tool_names(), indent=4, ensure_ascii=False) }")

if __name__ == "__main__":

    chatbot = MCP_ChatBot()
    # agent = ChatAgent(chatbot,[])
    # agent.list_BuiltIn_tools()
    asyncio.run(chatbot.main())