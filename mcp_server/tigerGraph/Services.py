#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
#
# tigerGraph_services.py: This modelue defines the TigerGraphService class 
# for acessing TigerGraph services to the graph database
#******************************************************************************
import sys
import re
import csv
import json
import datetime
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Union, Literal

from pyTigerGraph import TigerGraphConnection
from mcp_server.config import OUTPUT_PATH, tigerGraphConstants
from mcp_server.tigerGraph.interface import TigerGraphInterface
from mcp_server.tigerGraph.session import TigerGraph_Session
#
#intialize TigerGraph Constants by reading .env file
#
OUTPUT_PATH = tigerGraphConstants(output=True)

#
# The assumption is that you have setup (at a minumum) a user and password
# in your Tigergraph database
#
class TigerGraphServices(TigerGraphInterface):
    """
    Encapsulates all TigerGraph operations for MCP.
    Assumption that TigerGraph server is up and running 
    with a user id defined
    """
    def __init__(self):
        self.session = TigerGraph_Session()
        self.session.getConnection()
        self.initOutputDir()

    def initOutputDir(self):
        self.output_path = Path(OUTPUT_PATH)
        if not self.output_path.exists():
            Path.mkdir(self.output_path, exist_ok=True)


    def getConnection(self) -> TigerGraphConnection:
        return self.session.getConnection()

    def getGraphName(self) -> str:
        return self.session.graphName
    
    def get_schema(self):
        return self.getConnection().getSchema(force=True)

    def run_query(self, query_name: str, params: dict, outputFormat:Literal["Terminal","CSV","JSON"]="Terminal", timeout:int=60):
        """Runs a GSQL query and processes the output.

        Args:
            query:
                The text of the query to run as one string. The query is one or more GSQL statement.
            params:
                A dictionary of parameters to pass into query.
            timeout: Maximum duration for successful query execution (in seconds)
            """
        results = self.getConnection().runInstalledQuery(query_name, params, timeout=(timeout*1000))
        self.emptyResults = self.isResultSetEmpty(query_name, results)
        if self.emptyResults == False:
            if outputFormat.lower() == 'terminal':
                return(f"{json.dumps(results, indent=4, separators=(',', ':'))}")                            
            if outputFormat.lower() == 'csv':
                outputFile = f"{OUTPUT_PATH}/{query_name}.csv"
                self.json_to_csv(results, outputFile)
                return(f"\nWriting Query Results to {outputFile}")
            elif outputFormat.lower() == 'json':
                outputFile = f"{OUTPUT_PATH}/{query_name}.json"
                with open(outputFile, 'w', encoding='utf-8') as file:                                    
                    json.dump(results, file, indent=4, separators=(',', ':'))
                return(f"\nWriting Query Results to {outputFile}")
        else:
            return ""
        
    def json_to_csv(self, json_data, csv_filename):
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
                    
            # Extract all possible keys dynamically
            resultRow = list()
            for entry in json_data:
                self._writeCSV_header(writer, entry)
                self._writeCSV_values(writer, entry, resultRow)

    def _writeCSV_header(self, writer, entry):
        try:
            header_keys = list()
            for aResultSet in entry:
                anObject = entry.get(aResultSet)
                if isinstance(anObject,list):
                    for row in anObject:
                        if isinstance(row,dict):
                            if len(row.get("v_type",{})) > 0:
                                header_keys.append("v_type")
                                for attr in row.get("attributes", {}).keys():
                                    header_keys.append(attr)
                            elif len(row.get("e_type",{})) > 0:
                                for attr in row:
                                    if (attr == 'attributes'):
                                        for attr in row.get("attributes", {}).keys():
                                            header_keys.append(attr)
                                    else:
                                        header_keys.append(attr)
                            else:
                                for attr in row:
                                    header_keys.append(attr)
                        else:
                            header_keys.append(aResultSet)
                        break
                else:
                    header_keys.append(aResultSet)

                    # Write header row
            writer.writerow(header_keys)
        except Exception as e:
            print(f"Error in _writeCSV_header:")
            #traceback.print_exc()

    def _writeCSV_values(self, writer, entry, resultRow):
        try:
            for aResultSet in entry:
                anObject = entry.get(aResultSet)
                if isinstance(anObject,list):                    
                    for row in anObject:
                        resultRow = list()
                        if isinstance(row,dict):
                            if len(row.get("v_type",{})) > 0:
                                resultRow.append(row.get("v_type",{}))
                                for attr in row.get("attributes", {}).keys():
                                    value = row.get("attributes", {}).get(attr)
                                    if isinstance(value, list):
                                            # print('"' + ', '.join(map(str, value))+ '"')
                                        resultRow.append(', '.join(map(str, value)))
                                    else:
                                        resultRow.append(row.get("attributes", {}).get(attr))
                            elif len(row.get("e_type",{})) > 0:
                                for attr in row:
                                    if (attr == 'attributes'):
                                        resultRow.append(row.get("attributes", {}).get(attr))
                                    else:
                                        resultRow.append(row.get(attr))

                                    # Write row dynamically
                            else:
                                for attr in row:
                                    resultRow.append(row.get(attr))
                            
                            writer.writerow(resultRow)
                        else:
                            resultRow.append(row)
                            writer.writerow(resultRow)
                else:
                    resultRow.append(anObject)
                    writer.writerow(resultRow)
            writer.writerow([])
        except Exception as e:
            print(f"Error in _writeCSV_values:")
            #traceback.print_exc()

    def isResultSetEmpty(self, queryName, results):
        self.emptyResults=False
        if len(results) == 0 or results is None:
            print(f"No output found for query {queryName}...", file=sys.stderr)
            self.emptyResults=True
            return self.emptyResults
                        
        if not self.emptyResults:
            for dic in results:
                for key in dic.keys():
                    value = dic.get(key)
                    if isinstance(value, (str, list, dict, set)):
                        self.emptyResults = not bool(value)
                    else:
                        self.emptyResults = (value == 0)
                            
            if self.emptyResults:        
                print(f"No output found for query {queryName}...", file=sys.stderr)
        return self.emptyResults


    def show_query(self, query_name: str):
        return self.getConnection().showQuery(query_name)

    def get_installed_queries(self) -> Union[dict, str, 'pd.DataFrame']:
        return self.getConnection().getInstalledQueries()
    
    def define_vertex(self, vertex_type: str, vertex_id_name: str, attributes: dict) -> bool:
        """
        Generate a GSQL schema change job to define a vertex type with specified attributes.
        
        Args:
            vertex_name (str): The name of the vertex type (e.g., 'Firm', 'Person')
            id_field_name (str): The name of the primary ID field (e.g., 'firm_id', 'person_id')
            attributes (dict): Dictionary of attribute names and their data types
                            Format: {"attribute_name": "data_type"}
                            Valid types: STRING, INT, FLOAT, BOOL, DATETIME, etc.
        
        Prompt: define_vertex_prompt() -> defined on mcp_server.py

        Returns:
            str: Complete GSQL schema change job to add the vertex type
        """
        try:
            # Create a unique job name based on vertex name
            job_name = f"add_{vertex_type.lower()}_vertex_job"
            
            # Start building the GSQL schema change job
            gsql_parts = [
                f"USE Graph {self.getGraphName()}\n",
                f"CREATE SCHEMA_CHANGE JOB {job_name} {{\n",
                f"  ADD VERTEX {vertex_type} (",
                f"PRIMARY_ID {vertex_id_name} STRING"
            ]
            if len(attributes) >= 1:
                gsql_parts.append(f", ")            
            # Add each attribute with its data type
            self.addAttributes(attributes, gsql_parts,"")
            
            # Close the vertex definition with PRIMARY_ID_AS_ATTRIBUTE option
            gsql_parts.append(f") WITH PRIMARY_ID_AS_ATTRIBUTE=\"true\";\n")
            gsql_parts.append("}\n")
            gsql_parts.append(f"RUN SCHEMA_CHANGE JOB {job_name}")
            
            dropJob = f"DROP JOB {job_name}"
            results = self.getConnection().gsql(dropJob)

            gsqlAddVertex = "".join(gsql_parts)
            #print(f">>> gsql AddVertex: {gsqlAddVertex}", file=sys.stderr)
            
            results = self.getConnection().gsql(gsqlAddVertex,self.getGraphName())
            if isinstance(results, str):
                print(f"*** Define Vertex Results >>>: {results}", file=sys.stderr)

            dropJob = f"DROP JOB {job_name}"
            results = self.getConnection().gsql(dropJob)
            print(f"Drop Vertex Results: {results}", file=sys.stderr)
            return True
        except Exception as error:
            print(f"Error in define_vertex(): {error}", file=sys.stderr)
            return False

    def addAttributes(self, attributes:dict, gsql_parts:list, operator:str):
        attr_count = len(attributes)
        for i, (attr_name, attr_type) in enumerate(attributes.items()):
            comma = ', ' if i < attr_count - 1 else ''
            if (operator == "DROP"):
                gsql_parts.append(f"{attr_name}{comma}")
            else:
                gsql_parts.append(f"{attr_name} {self.infer_gsql_type(attr_type)}{comma}")

    def getVectorAttribute(self, attributes:dict) -> str:
        for i, (attr_name, attr_type) in enumerate(attributes.items()):
            if (attr_type == "VECTOR"):
                attributes.pop(attr_name)
                return attr_name
        return ""
    
    def alter_vertex(self, vertex_type:str, operator:Literal["ADD", "DROP"], attributes:dict={}, vector_attributes:dict={}) -> bool:
        """
        Generate a GSQL schema change job to alter a vertex type with specified attributes.
        Suppports Vector attributes with sepeaate vector attribute list. 
        Note: Only one Vector attribute can be altered per alter_vertex() function call
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
        try:
            # Create a unique job name based on vertex name
            job_name = f"alter_{vertex_type.lower()}_vertex_job"
            
            # Start building the GSQL schema change job
            gsql_parts = [
                f"USE Graph {self.getGraphName()}\n",
                f"CREATE SCHEMA_CHANGE JOB {job_name} {{\n",
                f"  ALTER VERTEX {vertex_type} {operator}",
            ]
            #
            # Retrieve the Vector attribute name from the list of vector_attributes
            #
            vectorName = self.getVectorAttribute(vector_attributes)
            if len(vectorName) > 0:
                gsql_parts.append(f" VECTOR ATTRIBUTE {vectorName}")
                if operator == "ADD":
                    gsql_parts.append(f"(")
                    attr_count = len(vector_attributes)
                    for v, (v_attr_name, v_attr_type) in enumerate(vector_attributes.items()):
                        comma = ', ' if v < attr_count-1 else ''
                        gsql_parts.append(f"{v_attr_name}={self.infer_vector_type(v_attr_type)}{comma}")
                
                    gsql_parts.append(f");\n")
                else:
                    gsql_parts.append(f";\n")


            elif len(attributes) > 0:
                gsql_parts.append(f" ATTRIBUTE (")
                # Add each attribute with its data type             
                self.addAttributes(attributes, gsql_parts, operator)
                gsql_parts.append(f");\n")

            gsql_parts.append("}\n")
            gsql_parts.append(f"RUN SCHEMA_CHANGE JOB {job_name}")           
            gsqlAlterVertex = "".join(gsql_parts)
            print(f">>> gsql AlterVertex: {gsqlAlterVertex}", file=sys.stderr)

            dropJob = f"DROP JOB {job_name}"
            results = self.getConnection().gsql(dropJob)

            results = self.getConnection().gsql(gsqlAlterVertex,self.getGraphName())
            if isinstance(results, str):
                print(f"*** Alter Vertex Results >>>: {results}", file=sys.stderr)
                results = self.getConnection().gsql(dropJob)
            return True
        
        except Exception as error:
            print(f"Error in alter_vertex(): {error}", file=sys.stderr)
            return False       

    def define_edge(self, edge_name: str, from_vertex: str, to_vertex: str, edge_type:Literal["UNDIRECTED", "DIRECTED"],
                          attributes: Dict[str, Any]={}, discriminator: Dict[str, Any]={}) -> bool:
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
        try:
            # Create a unique job name based on vertex name
            job_name = f"add_edge_job"
                    
            gsql_parts = [
                f"USE Graph {self.getGraphName()}\n",
                f"CREATE SCHEMA_CHANGE JOB {job_name} {{\n",
                f"   ADD {edge_type} EDGE {edge_name} (FROM {from_vertex}, TO {to_vertex}"
            ]

            # Add discriminator attributes first, (if specified) with its data types
            discriminator_count = len(discriminator)
            if discriminator_count > 0:
                gsql_parts.append(f", DISCRIMINATOR(")
                for i, (attr_name, attr_type) in enumerate(discriminator.items()):
                    comma = ',' if i < discriminator_count - 1 else ''
                    gsql_parts.append(f"{attr_name} {self.infer_gsql_type(attr_type)}{comma}")
                gsql_parts.append(f")")

            # Add each attribute with its data type
            attr_count = len(attributes)
            if attr_count == 1:
                gsql_parts.append(f",")
            for i, (attr_name, attr_type) in enumerate(attributes.items()):
                comma = ',' if i < attr_count - 1 else ''
                gsql_parts.append(f"{comma} {attr_name} {self.infer_gsql_type(attr_type)}{comma}")
            
            # Close the Edge definition with Roption
            if (edge_type == "UNDIRECTED"):
                gsql_parts.append(f");\n")
            else:
                gsql_parts.append(f") WITH REVERSE_EDGE=\"reverse_{edge_name}\";\n")
            
            gsql_parts.append("}\n")
            gsql_parts.append(f"RUN SCHEMA_CHANGE JOB {job_name}")

            gsqlAddEdge = "".join(gsql_parts)
            print(f">>> gsql AddVertex: {gsqlAddEdge}", file=sys.stderr)

            dropJob = f"DROP JOB {job_name}"
            results = self.getConnection().gsql(dropJob)

            results = self.getConnection().gsql(gsqlAddEdge,self.getGraphName())
            if isinstance(results, str):
                print(f"*** Define Edge Results >>>: {results}", file=sys.stderr)

            dropJob = f"DROP JOB {job_name}"
            results = self.getConnection().gsql(dropJob)
            print(f"Drop Edge Results: {results}", file=sys.stderr)
            return True
        
        except Exception as error:
            print(f"Error in define_edge(), {error}")
            return False

    def infer_vector_type(self, attr_type):
        """
        Helper function to infer GSQL Vector type
        
        Args:
            sample_value: A sample value to infer the type from
        
        Returns:
            str: DIMENSION:INT, METRIC: "COSINE" or "L2" or "IP", INDEXTYPE:"HNSW", DATATYPE:"FLOAT"
        """
        INT="INT"
        FLOAT="FLOAT"
        L2="L2"
        IP="IP"
        COSINE="COSINE"
        HNSW="HNSW"
        if isinstance(attr_type, str):
            #test to see if sample_value is a date field
            match (str(attr_type).upper()):
                case "COSINE":
                    return f'"{COSINE}"'
                case "L2":
                    return f'"{L2}"'
                case "IP":
                    return f'"{IP}"'
                case "HNSW":
                    return f'"{HNSW}"'
                case "FLOAT":
                    return f'"{FLOAT}"'
        elif isinstance(attr_type, int):
            return attr_type


    def infer_gsql_type(self, attr_type):
        """
        Helper function to infer GSQL data type from either a sample value, 
        or Actual type defined as a string.
        
        Args:
            sample_value: A sample value to infer the type from
        
        Returns:
            str: GSQL data type (STRING, INT, FLOAT, BOOL)
        """
        INT="INT"
        BOOL="BOOL"
        FLOAT="FLOAT"
        STRING="STRING"
        DATETIME="DATETIME"
        VECTOR="VECTOR"

        try:
            if isinstance(attr_type, bool):
                return BOOL
            elif isinstance(attr_type, int):
                return INT
            elif isinstance(attr_type, float):
                return FLOAT
            elif isinstance(attr_type, str):
                #test to see if sample_value is a date field
                match (str(attr_type).upper()):
                    case "INT":
                        return INT
                    case "FLOAT":
                        return FLOAT
                    case "BOOL":
                        return BOOL
                    case "STRING":
                        return STRING
                    case "DATETIME":
                        return DATETIME
                    case "VECTOR":
                        return VECTOR
                if re.match(r'^\d{4}-\d{2}-\d{2}$', attr_type):
                    sampleDate = datetime.datetime.strptime(attr_type, '%Y-%m-%d')
                    if isinstance(sampleDate,datetime.datetime):
                        return DATETIME
                return STRING
        except ValueError as error:
            print(f"ERROR in gsql_type {error}")


    def upsert_vertex(self, vertex_type: str, vertex_id: str, attributes: dict) -> int:
        """ MCP tool: Update a vertex with data that is specified in the attributes.
            Args:
                vertex_type (str): The name of the vertex type (e.g., 'Firm', 'Person')
                vertex_id (str): The value of the primary ID field
                attributes (dict): Dictionary of attribute names and their data types
                            Format: {"attribute_name": "data_type"}

            Prompt: update_vertex_prompt() -> defined on mcp_server.py
        """
        return self.getConnection().upsertVertex(vertex_type, vertex_id, attributes)


    def upsert_edge(self, source_type: str, source_id: str, edge_type: str,
                    target_type: str, target_id: str, attributes: dict = {})  -> int:
        
        return self.getConnection().upsertEdge(source_type, source_id, edge_type,
                                    target_type, target_id, attributes or {})

    def get_vertex(self, vertex_type: str, vertex_id: str) -> Union[list, str, 'pd.DataFrame']:
        return self.getConnection().getVerticesById(vertex_type, vertex_id)

    def run_gsql(self, query: str):
        return self.getConnection().gsql(query=query, graphname=self.getConnection().graphname)

    def get_udf(self, ExprFunctions: bool = True, ExprUtil: bool = True, 
                json_out: bool = False) -> Union[Tuple[str, str], Dict[str, Any], str]:

        return self.getConnection().getUDF(ExprFunctions, ExprUtil, json_out)

