from typing import List

from abc import ABC, abstractmethod
from autogen import ChatResult 

from mcp_server.mcp_chatbot.mcp_services import MCPServices


class MCP_AgentInterface(ABC):
    """Abstract base class for all MCP based Agents."""

    def __init__(self):
        super().__init__()

   
    @abstractmethod    
    def getMCPServices(self) -> dict:    
        """
        Get the MCP Services, which consists of Tools, Prompts,
        and Resources.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def invokeAgent(self,query:str):
        """
        Method to invode an agent
        """
        raise NotImplementedError    