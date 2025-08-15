#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# agent_interface.py: ChatAgent interface to assure standard implementation
#******************************************************************************

from abc import ABC, abstractmethod


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