#******************************************************************************
# Copyright (c) 2025, Custom Discoveries Inc.
# All rights reserved.
# MCP_Server.py: This modelue defines the TigerGraph MCP Server and 
# the associated tools and prompts to support accessing TigerGraph services
#******************************************************************************
import sys
import warnings

from typing import Literal
from mcp.server.fastmcp import FastMCP
from mcp_server.tigerGraph.Services import TigerGraphServices
import logging

# Disable logger
warnings.filterwarnings('ignore')
logging.getLogger('mcp.server.lowlevel.server').disabled = True


class TigerGraph_MCP_Server():
    
    def __init__(self):
        self.mcp = FastMCP("TigerGraph MCP Server")
        self.services = TigerGraphServices()
        
        # Register tools directly
        self.mcp.tool()(self.get_schema)
        self.mcp.tool()(self.run_query)
        self.mcp.tool()(self.show_query)
        self.mcp.tool()(self.get_installed_query)
        self.mcp.tool()(self.define_vertex)
        self.mcp.tool()(self.update_vertex)
        self.mcp.tool()(self.alter_vertex)
        self.mcp.tool()(self.define_edge)
        self.mcp.tool()(self.update_edge)
        self.mcp.tool()(self.get_vertex)
        self.mcp.tool()(self.get_udf)
        
        # Register Prompts directly
        self.mcp.prompt()(self.define_vertex_prompt)
        self.mcp.prompt()(self.update_vertex_prompt)

    def get_schema(self):
        """MCP tool: Get TigerGraph Schema."""
        return self.services.get_schema()


    def run_query(self, query_name: str, params: dict = {}, timeout:int=60):
        """ MCP tool: Run a TigerGraph query with parameters.
            Args:
                query:
                    The name of the query to run.
                params:
                    A dictionary of parameters to pass into query.
                timeout: Maximum duration for successful query execution, in seconds (default=60 seconds)
                """
        return self.services.run_query(query_name, params, timeout=timeout)

    def show_query(self, query_name: str):
        """MCP tool: Retrieve the content of a GSQL query."""
        return self.services.show_query(query_name)


    def get_installed_query(self):
        """MCP tool: List all installed GSQL queries."""
        return self.services.get_installed_queries()


    def define_vertex(self, vertex_type: str, vertex_id_name: str, attributes: dict):
        """MCP tool: Define a vertex in TigerGraph database.
        Prompt: define_vertex_prompt()
        """
        return self.services.define_vertex(vertex_type, vertex_id_name, attributes)

    def update_vertex(self, vertex_type: str, vertex_id: str, attributes: dict):
        """MCP tool: Update a vertex with data that is specified in the attributes.
        Prompt: update_vertex_prompt()
        """
        return self.services.upsert_vertex(vertex_type, vertex_id, attributes)


    def alter_vertex(self, vertex_type:str, operator:Literal["ADD", "DROP"], attributes:dict={}, vector_attributes:dict={}) -> bool:
        """MCP tool: Alter's vertex attributes.
        """
        return self.services.alter_vertex(vertex_type, operator, attributes, vector_attributes)


    def define_edge(self, edge_name: str, from_vertex: str, to_vertex: str, edge_type:Literal["UNDIRECTED", "DIRECTED"],
                    attributes: dict = {}, discriminator: dict = {}):
        """ MCP tool: Define an edge.
            Args:
                edge_name (str): The name of the edge (e.g., 'isPartOf', 'isLocatedIn')
                from_vertex (str): The name of the from vertex
                to_vertex (str): The name of the to vertex
                edge_type (str): Either one of the two options: 'UNDIRECTED' or 'DIRECTED'
                attributes (dict): Dictionary of attribute names and their data types
                discriminator (dict): DISCRIMINATOR - Dictionary of attribute names and types that defines a discriminator
                                        in an edge type definition to allow multiple instances of an edge type between 
                                        two vertices.
        """
        return self.services.define_edge(edge_name, from_vertex, to_vertex, edge_type, attributes, discriminator)


    def update_edge(self, source_type: str, source_id: str, edge_type: str,
                    target_type: str, target_id: str, attributes: dict = {}):
        """MCP tool: update an defined edge between a source and a target vertex."""
        return self.services.upsert_edge(source_type, source_id, edge_type, target_type, target_id, attributes)


    def get_vertex(self, vertex_type: str, vertex_id: str):
        """MCP tool: Retrieve a vertex by type and ID."""
        return self.services.get_vertex(vertex_type, vertex_id)

    # @mcp.tool()
    # def run_gsql(query: str):
    #     """MCP tool: Run a raw GSQL query."""
    #     return client.run_gsql(query)


    def get_udf(self, ExprFunctions: bool = True, ExprUtil: bool = True, json_out=False):
        """MCP tool: Get UDF files."""
        return self.services.get_udf(ExprFunctions, ExprUtil, json_out)


    def define_vertex_prompt(self) -> str:
        """ This prompt is designed to be used with a Desktop Agent, like Anthropic Claude.
            Generate a prompt for LLM to define a vertex using the TigerGraph define_vertex api.
        """
        return f"""Using the define_vertex api, define a vertex in TigerGraph using a nested dictionary, with 
        special attention to how the vertex name and vertex ID are extracted.

    Follow these instructions:
    1. First, use the define_vertex tool to define a vertex. Pass in the name of the vertex and the name of the vertex id attribute.
    2. You will receive a dictionary, with the format of key:value. Using the key of the dictionary as the vertex name,
    Format it as a proper noun, capitalizing the first character for the vertex name.
    2. Next, the value of the dictonary will point to another dictonary, (key:(Key:Value)i.e. Embedded dictionary). 
    This important, use the KEYS of the 2nd dictionary to determine the vertex attributes names.
    3. Set the the vertex_id attribute with a strng, using the 'Key' and NOT the key value. Find an attribute with 'id' 
    as part of the name, and use that name as the vertex_id name.  As an example: the vertex_id would = "firm_nid", not the value: 2025 
    The vertexId name would be firm_nid as the last two characters has id in the name.
    4. Pass the rest of the list, excluding the id that you use for the vertex_id name to the define_vertex api call.
    5. Change any attirbute key that has a space to a "_"
    6. Change the attirbute if there is a type of "null" to "". Do not change any other of the attibutes types, if they is a
    datetime, integer, or float to not pass these attributes as string values.
    7. Check the status of the TigerGraph database by performing a get_schema api call
    8. If the vertex is not found, do not try any other means to create the vertex!"""


    def update_vertex_prompt(self) -> str:
        """ This prompt is designed to be used with a Desktop Agent, like Anthropic Claude.
            Generate a prompt for LLM to update a vertex using the TigerGraph update_vertex api.
        """
        return f"""Using the update_vertex api,update a vertex in TigerGraph using a vertex_type, vertex_id, and
        a dictionary of vertex attributes to update.

    Follow these instructions:
    1. First, use the update_vertex tool to update data on an exiting defined vertex. There are 3 parameters: vertex_type
    which identifies the vertex type to update. Vertex_id identify which instance of the Vertex type to update. Finally
    the attributes dictonary contain the the attibute name and the values that should be updated.
    2. You will receive a dictionary, with the format of key:value. Using the key of the dictionary as the attribute name,
    and the value of the dictonary to update the vertex attribute with the new data.
    3. Check the status of the TigerGraph database by performing a get_vertex api call using the vertex name and vertex id"""

    def run_server(self):
        """Run server"""

        try:
            print(f"Please Standby, Starting Up TigerGraph MCP Server for Graph {self.services.getGraphName()} ...", file=sys.stderr)
            self.mcp.run(transport='stdio')

        except Exception as error:
            print(f"Error Occured in tg_mcp_server main(): {error}", file=sys.stderr)


if __name__ == "__main__":
    server = TigerGraph_MCP_Server()
    server.run_server()

