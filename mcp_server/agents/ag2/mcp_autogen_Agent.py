import os
import sys
import asyncio
import traceback

from typing import Any, Annotated, Dict, List, Optional

from autogen import ConversableAgent, LLMConfig, UpdateSystemMessage
from autogen.agentchat import initiate_group_chat, a_initiate_group_chat
from autogen.tools import Toolkit

from autogen.agentchat.group import (AgentTarget,
                                     AgentNameTarget,
                                     ContextVariables,
                                     RevertToUserTarget,
                                     OnCondition,
                                     StringLLMCondition,
                                     TerminateTarget,
                                     )
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.mcp import create_toolkit

from mcp import ClientSession
from mcp_server.prompts.contextAwarePrompts import (directoryPrompt, 
                                                    tigerGraphPrompt, 
                                                    routingPrompt
                                                    )
from mcp_server.toolBoxes.agentToolBox import classify_query


from mcp_server.config import initialLLMConstants, getLLMConstants, getALLFamilyLLMConstants
from mcp_server.mcp_logger import setErrorHandler
promptCache = {}


LLM_MODEL_FAMILY = initialLLMConstants()
GOOGLE, OPENAI,ANTHROPIC = getALLFamilyLLMConstants()
API_KEY, LLM_MODEL, TOKENS = getLLMConstants(LLM_MODEL_FAMILY)

class MCP_Agent:

    def __init__(self, agentName:str):

        promptCache.update({"filesystem":directoryPrompt})
        promptCache.update({"tigerGraph":tigerGraphPrompt})

        self.llm_config = LLMConfig(api_type=LLM_MODEL_FAMILY.lower(),
                                    model=LLM_MODEL,
                                    api_key=API_KEY,
                                    temperature=0,
                                    tool_choice="required",
                                    )
        
        self.ag2Agent = ConversableAgent(
            name=agentName,
            system_message=promptCache.get(agentName),
            llm_config=self.llm_config,
        )

    def getAgent(self) -> ConversableAgent:
        return self.ag2Agent

    async def create_mcp_toolKit(self, session: ClientSession) -> List[Toolkit]:
        try:
            self.toolkit = await create_toolkit(session=session,use_mcp_tools=True,
                                                use_mcp_resources=False)
            self.toolkit.register_for_llm(self.ag2Agent)
            self.toolkit.register_for_execution(self.ag2Agent)
            self.ag2Agent.handoffs.set_after_work(TerminateTarget())
            
            return self.toolkit.tools
        
        except Exception as error:
            print(f"Error in create_mcp_toolKit(): {error}")

            

class ChatAgent:
    """
    ChatAgent class is used to support AG2 Agent based soltuion
    """

    def __init__(self):
        
        setErrorHandler()

        # Shared context for tracking the conversation and routing decisions
        self.shared_context = ContextVariables(data={
            # Routing state
            "routing_started": False,
            "current_tool": None,
            "previous_tool": [],
            "agent_tool_list": {},
            "tool_confidence": {},

            # Request tracking
            "request_count": 0,
            "current_request": "",
            "tool_history": {},

            # Response tracking
            "question_responses": [], # List of question-response pairs
            "question_answered": True, # Indicates if the last question was answered


            # Error state (not handled but could be used to route to an error agent)
            "has_error": False,
            "error_message": "",
        })

        try:
            self.llm_config = LLMConfig( api_type=LLM_MODEL_FAMILY.lower(),
                                    model=LLM_MODEL,
                                    api_key=API_KEY,
                                    tool_choice="required",
                                    temperature=0
                                    )

            #systemMessage=f"""As a router agent, here is your list of tool agents, and their associated tools that you can route to, based on user request for using a tool\n"""
            self.routerAgent = ConversableAgent(
                name="router_agent",
                llm_config=self.llm_config,
                system_message=routingPrompt,
                functions=[classify_query]
                )


        except Exception as error:
            print(f"Error in ChatAgent.init(): {error}")
 
    async def create_mcp_toolKit(self, serverName:str, session: ClientSession) -> List[Toolkit]:
        
        mcpAgent:MCP_Agent = self.createMCPAgent(serverName)
        #(self.shared_context.data.get("agent_tool_list")).get(serverName)
        listOfTools = await mcpAgent.create_mcp_toolKit(session)
        
        print(f"Number of tools found for {serverName} = {len(listOfTools)}")

        return listOfTools

    
    def createMCPAgent(self, serverName:str) -> MCP_Agent:

        try:
            mcpAgent:MCP_Agent = MCP_Agent(serverName)
            self.shared_context.data.get("agent_tool_list").update({serverName:mcpAgent})
            
            return mcpAgent
        
        except Exception as error:
            print(f"Error in createMCPAgent() function: {error}",file=sys.stderr)


    def getToolAgents(self, agentName:str=None) -> ConversableAgent:

 
        agentList:List[ConversableAgent] = []

        tools:dict = self.shared_context.data.get("agent_tool_list")
        if agentName == None or agentName == "":
            for agent in tools.values():
                agentList.append(agent.getAgent())
        else:
            agent = tools.get(agentName)
            agentList.append(agent.getAgent())
    
        return agentList

    def getToolsNames_w_Descriptions(self,agentName:Optional[str]=None) -> List[str]:
        
        toolList:List[str] = []
        tools:dict = self.shared_context.data.get("agent_tool_list")
        if agentName == None or agentName == "":
            for anAgent in tools.values():
                for item in anAgent.toolkit.tools:
                    toolList.append(item.name)
        else:
            anAgent = tools.get(agentName)
            for item in anAgent.toolkit.tools:
                toolList.append(f"{item.name} - {item.description}")
    
        return toolList
    
    def getToolsNames(self,agentName:Optional[str]=None) -> List[str]:
        
        toolList:List[str] = []
        tools:dict = self.shared_context.data.get("agent_tool_list")
        if agentName == None or agentName == "":
            for anAgent in tools.values():
                for item in anAgent.toolkit.tools:
                    toolList.append(item.name)
        else:
            anAgent = tools.get(agentName)
            for item in anAgent.toolkit.tools:
                toolList.append(item.name)
    
        return toolList

    def getAgentFromToolBox(self, agentName:str) -> ConversableAgent:
        return AgentNameTarget(agentName)
    

    def registerAgents(self):
        #
        # Update the tool agents
        #
        agentList:List[ConversableAgent] = self.getToolAgents()

        for agent in agentList:
            self.routerAgent.handoffs.add(
                OnCondition(
                    target=AgentTarget(agent),
                    condition=StringLLMCondition("Return to the router after your tool execution has been compiled.")
                    ),
                )
            self.routerAgent.handoffs.add_llm_conditions(
                [OnCondition(
                    target=AgentTarget(agent),
                    condition=StringLLMCondition(prompt=f"The {agent.name} has finish executing")
                )]
            )
      
      
        #
        # Add Router to the list of agents
        #
        agentList.append(self.routerAgent)
        #
        # Reset all agents
        #    
        for agent in agentList:
            agent.reset()

        self.agent_pattern = DefaultPattern(
            agents=agentList,
            initial_agent=self.routerAgent,
            context_variables=self.shared_context,
        )

    def run(self,query:str):
        
        response = self.toolAgent.getAgent().run(
            message=query,
            user_input=False
        )
        response.process()
        size = len(response.messages)
        print(response.messages[size-1]['content'])

    async def invokeAgent(self,query:str):
        try:
            result, context, last_agent = await a_initiate_group_chat(
                pattern=self.agent_pattern,
                messages=query,
                max_rounds=100,
            )
            print(f"Last Agent = {last_agent}")
            return result
        except Exception as error:
            traceback.print_exc()
            print(f"Error in invokeAgent() {error}")

    def router_content_updater(self, agent: ConversableAgent, messages: List[Dict[str, Any]]) -> str:
        message_string:str=f"""As a router agent, here is your list of tool agents, and their associated tools that you can route to, based on user request for using a tool\n"""

        for key, value in messages.items():
                message_string = (f"{message_string} agent: {key}, and list of tools:\n")
                for tool in value.toolkit.tools:
                     message_string = (f"{message_string}   {tool.name}\n")
        
        return message_string


    def tool_content_updater(self, agent: ConversableAgent, messages: List[Dict[str, Any]]) -> str:
        message_string:str=f"As a {agent.name} tool agent, here is your list of tools that you can execute on:\n"
        agent_name = agent.name
        agent_tools = self.getToolsNames_w_Descriptions(agent_name)
        for tool in agent_tools:
            message_string = (f"{message_string} {tool}\n")
        
        return message_string


    def getLLM(self) -> ConversableAgent:
        return self.agent
    
    def getTools(self) -> List:
        return self.toolkit.tools

    def list_BuiltIn_tools(self):
        #return print(f"List of Tools: {json.dumps(get_all_tool_names(), indent=4, ensure_ascii=False) }")
        print(f"List of Tools: {self.toolkit.tools}")

