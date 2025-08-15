#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# chatAgent.py: This modelue defines classes, RunMCPServer(), ChatAgent 
#******************************************************************************
import traceback

from typing import Annotated, List, Union
from mcp.types import CallToolResult

from autogen import (AssistantAgent,
                     UserProxyAgent,
                     LLMConfig,
                     UpdateSystemMessage
                     )
from autogen.runtime_logging import start, stop

from autogen.agentchat import initiate_group_chat

from autogen.agentchat.group import ContextVariables
from autogen.agentchat.group.patterns import DefaultPattern

from mcp_server.agents.prompts.toolKitPrompt import processing_prompt, pretty_print_prompt

from mcp_server.agents.toolBoxes.mcpToolBox import record_mcp_params

from mcp_server.config import initialLLMConstants, getLLMConstants, getALLFamilyLLMConstants
from mcp_server.mcp_chatbot.mcp_services import MCPServices
from mcp_server.agents.agent_interface import MCP_AgentInterface
from mcp_server.mcp_logger import setErrorHandler, logging, logger

# Set AG2 logging to only show errors
logging.getLogger("autogen").setLevel(logging.WARNING)
logging.getLogger("autogen_core").setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)  # Optional: silence all root loggers


LLM_MODEL_FAMILY = initialLLMConstants()
ANTHROPIC, OPENAI, GOOGLE = getALLFamilyLLMConstants()
API_KEY, LLM_MODEL, TOKENS = getLLMConstants(LLM_MODEL_FAMILY)

class RunMCPServer():

    def __init__(self, mcpServices:MCPServices):
        self.mcpServices:MCPServices = mcpServices
        setErrorHandler()

    
    async def call_mcp_server(self,
                 server_name: Annotated[str, "Name of MCP_Server to use"],
                 tool_name: Annotated[str, "Name of tool to use"],
                 attributes: Union[Annotated[dict, "Input parametes to run MCP call_tool"], None],
                 context_variables: ContextVariables
                 ) -> List:
        try:

            if not server_name:
                context_variables["mcp_call_status"] = False
            else:
                context_variables["mcp_call_status"] = True

            mcpService:MCPServices = self.mcpServices[server_name]
            session = mcpService.getToolSession(tool_name)
            logger.info(f"Calling MCP Tool: {tool_name} with attributes: {attributes}")

            response = await session.call_tool(tool_name, arguments=attributes)
            if response.isError:
                context_variables["mcp_call_status"] = False
                logger.error(f"MCP call_tool, error in answer, {tool_name} {attributes}")
            else:
                context_variables["mcp_call_status"] = True
                context_variables["completed_stage"] = "CALL_TOOL_SUCCESS"
                #context_variables["answer"]=answer
            
            if isinstance(response,CallToolResult):
                answer = []
                for item in response.content:
                    answer.append(item.text)

                return answer
                   
        except Exception as error:
            #print(f"Error in call_mcp_server(): {error}")
            context_variables["mcp_call_status"] = False
            context_variables["error_message"] = error
        
        return None
    
class ChatAgent(MCP_AgentInterface):
    """
    ChatAgent class is used to support AG2 Agent based soltuion
    """
    listOfTools = None

    def __init__(self,mcpServices:MCPServices):

        self.llm_config = LLMConfig( api_type=LLM_MODEL_FAMILY.lower(),
                                    model=LLM_MODEL,
                                    api_key=API_KEY
                                    )  

        setErrorHandler()
        self.mcpServices = mcpServices
        self.mcp_server = RunMCPServer(self.mcpServices)
      
        # Shared context for tracking the conversation and routing decisions
        self.shared_context = ContextVariables(data={
            # Routing state
            "server_name":"",
            "tool_name":"",
            "attributes":"",
            "query":"",
            "listOfTools":"",
            "mcp_call_status":False,
            "answer":None,
            "completed_stage":None,
            "error_message": "",
        })

        with self.llm_config:
            """Create MCP lookup agent for finding mcp tool to use"""
            self.toolAgent = AssistantAgent(
                name="lookup_tool",
                functions=[record_mcp_params],
                # Make sure to update the ContextVariables before
                # calling UpdateSystemMessage
                update_agent_state_before_reply=[
                    UpdateSystemMessage(processing_prompt)],
                )
            """Create Pretty Print agent for formatting output"""
            self.prettyPrint = AssistantAgent(
                name="pretty_printer",
                max_consecutive_auto_reply=1,
                human_input_mode="NEVER",
                system_message=pretty_print_prompt,
            )

            """Create user proxy agent for human interaction"""
            self.human = UserProxyAgent(
                name="human_agent",
                code_execution_config={"use_docker": False},
                llm_config=self.llm_config
            )

        #
        # Create a Group Chat of 1, so that we
        # can use the context_variables feature
        #
        self.pattern = DefaultPattern(
            initial_agent=self.toolAgent,  # Agent that starts the conversation
            agents=[self.toolAgent],
            context_variables=self.shared_context,
            user_agent=self.human
            )

    async def invokeAgent(self,query:str):
        try:
            self.shared_context["query"] = query
            self.shared_context["listOfTools"] = self.getToolNamesToString()

            chat_result, _, _ = initiate_group_chat(
            pattern=self.pattern,
            max_rounds=10,
            messages="run the record_mcp_params tool")

            if len(chat_result.summary) > 0:
                server_name = self.shared_context.data.get("server_name")
                tool_name = self.shared_context.data.get("tool_name")
                attributes = self.shared_context.data.get("attributes")
                if attributes == 'None':
                    attributes = {}
                response = await self.mcp_server.call_mcp_server(
                                                server_name,
                                                tool_name,
                                                attributes,
                                                self.shared_context)
                
            if self.shared_context.data.get("mcp_call_status",False) == True:
                prompt = f"Pretty print the follwoing list {response}"
                formatted_output = self.prettyPrint.run(message=prompt)
                return formatted_output
            else:
                return f"Error in invokeAgent() {self.shared_context.data.get('error_message')}"

        except Exception as error:
            traceback.print_exc()
            print(f"Error in invokeAgent() {error}")

    def getMCPServices(self) -> dict:
            return self.mcpServices

    async def callMCPAgent(self,query:str):
        response = await self.invokeAgent(query)
        return response

    def list_BuiltIn_tools(self):
        pass
        #return print(f"List of Tools: {json.dumps(get_all_tool_names(), indent=4, ensure_ascii=False) }")
        #print(f"List of Tools: {self.toolkit.tools}")

    def getToolNamesToString(self) -> str:
        formatted_tools="\n"
        mcp_services:MCPServices
        total_tool_list:List = []
        #
        # Loop through all of the MCP Services (Servers) and 
        # get a complete list of all the tools that are connected
        #
        for mcp_services in self.getMCPServices().values():
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

