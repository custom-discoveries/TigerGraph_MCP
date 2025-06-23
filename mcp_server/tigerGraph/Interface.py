#******************************************************************************
# Copyright (c) 2025, Custom Discoveries Inc.
# All rights reserved.
#
# TigerGraphInterface.py: This modelue defines the interfaces that support the
# TigerGraph MCP Server and the associated services
#******************************************************************************
import pandas as pd

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Union, Literal


class TigerGraphInterface(ABC):
    """
    Abstract interface for TigerGraph database operations.
    
    This interface defines the contract that any TigerGraph client implementation
    must follow to provide consistent access to TigerGraph database functionality.
    """

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the TigerGraph database schema.
        
        Returns:
            Dict[str, Any]: The database schema information including vertex types,
                          edge types, and their attributes.
        """
        pass

    @abstractmethod
    def run_query(self, query_name: str, params: Dict[str, Any] = {}, timeout: int = 60) -> Any:
        """
        Run a TigerGraph query with parameters.
        
        Args:
            query_name (str): The name of the query to execute.
            params (Dict[str, Any], optional): Dictionary of parameters to pass to the query.
                                             Defaults to None.
            timeout (int, optional): Maximum duration for successful query execution in seconds.
                                   Defaults to 60 seconds.
        
        Returns:
            Any: The query execution results.
        
        Raises:
            TimeoutError: If the query execution exceeds the timeout duration.
            ValueError: If the query_name is invalid or parameters are malformed.
        """
        pass

    @abstractmethod
    def show_query(self, query_name: str) -> str:
        """
        Retrieve the content of a GSQL query.
        
        Args:
            query_name (str): The name of the query to retrieve.
        
        Returns:
            str: The GSQL query content as a string.
        
        Raises:
            ValueError: If the query_name does not exist.
        """
        pass

    @abstractmethod
    def get_installed_queries(self) -> Union[dict, str, 'pd.DataFrame']:
        """
        List all installed GSQL queries.
        
        Returns:
            List[str]: A list of installed query names.
        """
        pass

    @abstractmethod
    def define_vertex(self, vertex_type: str, vertex_id_name: str, attributes: Dict[str, Any]) -> bool:
        """
        Define a vertex type in the TigerGraph database.
        
        Args:
            vertex_type (str): The name of the vertex type to define.
            vertex_id_name (str): The name of the primary key attribute for this vertex type.
            attributes (Dict[str, Any]): Dictionary mapping attribute names to their data types.
        
        Returns:
            bool: True if the vertex type was successfully defined, False otherwise.
        
        Raises:
            ValueError: If vertex_type or vertex_id_name is invalid.
        """
        pass

    @abstractmethod
    def upsert_vertex(self, vertex_type: str, vertex_id: str, attributes: Dict[str, Any]) -> int:
        """
        Insert or update a vertex with the specified attributes.
        
        Args:
            vertex_type (str): The type of the vertex.
            vertex_id (str): The unique identifier for the vertex.
            attributes (Dict[str, Any]): Dictionary of attribute names and their values.
        
        Returns:
            bool: True if the vertex was successfully upserted, False otherwise.
        
        Raises:
            ValueError: If vertex_type does not exist or attributes are invalid.
        """
        pass

    @abstractmethod
    def alter_vertex(self, vertex_type:str, operator:Literal["ADD", "DROP"], attributes:dict={}, vector_attributes:dict={}) -> bool:
        """
        Generate a GSQL schema change job to alter a vertex type with specified attributes.
        Args:
            vertex_type (str): The name of the vertex type (e.g., 'Firm', 'Person')
            operator (str): The alter operator can either be "ADD" or "DROP"
            
            attributes (dict): Dictionary of attribute names and their data types
                            Format: {"attribute_name": "data_type"}
                            Valid types: STRING, INT, FLOAT, BOOL, DATETIME etc.
            
            vector_attributes (dict): Dictionay of VECTOR attributes and types
                            Valid Names:types: some_name:"VECTOR", DIMENSION:INT, 
                                        METRIC: "COSINE" or "L2" or "IP", INDEXTYPE:"HNSW", DATATYPE:"FLOAT"
        
        Prompt: define_alter_prompt() -> defined on mcp_server.py

        Returns:
            str: Complete GSQL schema change job to alter the vertex attribute type
        """
        pass

    @abstractmethod
    def define_edge(self, edge_name: str, from_vertex: str, to_vertex: str, 
                   edge_type: Literal["UNDIRECTED", "DIRECTED"],
                   attributes: Dict[str, Any] = {}, 
                   discriminator: Dict[str, Any] = {}) -> bool:
        """
        Define an edge type in the TigerGraph database.
        
        Args:
            edge_name (str): The name of the edge type (e.g., 'isPartOf', 'isLocatedIn').
            from_vertex (str): The name of the source vertex type.
            to_vertex (str): The name of the target vertex type.
            edge_type (Literal["UNDIRECTED", "DIRECTED"]): The edge direction type.
            attributes (Dict[str, Any], optional): Dictionary of attribute names and their data types.
                                                 Defaults to None.
            discriminator (Dict[str, Any], optional): Dictionary of attribute names and types that 
                                                    defines a discriminator in an edge type definition 
                                                    to allow multiple instances of an edge type between 
                                                    two vertices. Defaults to None.
        
        Returns:
            bool: True if the edge type was successfully defined, False otherwise.
        
        Raises:
            ValueError: If edge_name, from_vertex, or to_vertex is invalid, or if edge_type 
                       is not "UNDIRECTED" or "DIRECTED".
        """
        pass

    @abstractmethod
    def upsert_edge(self, source_type: str, source_id: str, edge_type: str,
                   target_type: str, target_id: str, attributes: Dict[str, Any] = {}) -> int:
        """
        Insert or update an edge between a source and target vertex.
        
        Args:
            source_type (str): The type of the source vertex.
            source_id (str): The unique identifier of the source vertex.
            edge_type (str): The type of the edge.
            target_type (str): The type of the target vertex.
            target_id (str): The unique identifier of the target vertex.
            attributes (Dict[str, Any], optional): Dictionary of attribute names and their values.
                                                 Defaults to None.
        
        Returns:
            bool: True if the edge was successfully upserted, False otherwise.
        
        Raises:
            ValueError: If any of the vertex types or IDs are invalid, or if the edge_type 
                       does not exist.
        """
        pass

    @abstractmethod
    def get_vertex(self, vertex_type: str, vertex_id: str) -> Union[list, str, 'pd.DataFrame']:
        """
        Retrieve a vertex by its type and ID.
        
        Args:
            vertex_type (str): The type of the vertex to retrieve.
            vertex_id (str): The unique identifier of the vertex.
        
        Returns:
            Dict[str, Any]: The vertex data including all its attributes.
        
        Raises:
            ValueError: If the vertex_type does not exist.
            KeyError: If no vertex with the given vertex_id exists.
        """
        pass

    @abstractmethod
    def get_udf(self, ExprFunctions: bool = True, ExprUtil: bool = True, 
               json_out: bool = False) -> Union[Tuple[str, str], Dict[str, Any], str]:
        """
        Get User Defined Functions (UDF) information.
        
        Args:
            ExprFunctions (bool, optional): Whether to include expression functions. 
                                          Defaults to True.
            ExprUtil (bool, optional): Whether to include expression utilities. 
                                     Defaults to True.
            json_out (Union[bool, str], optional): Whether to return JSON output format. 
                                                 Defaults to False.
        
        Returns:
            Union[Tuple[str, str], Dict[str, Any], str]: UDF information as a dictionary or JSON 
            string, depending on json_out parameter.
        """
        pass

