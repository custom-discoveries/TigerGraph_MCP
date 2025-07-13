#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
#
# tigerGraph_Session.py: This modelue defines the TigerGraphSession class for
# managing TigerGraph authenitcation and session to the graph database
#******************************************************************************
import sys
import logging
import traceback

from requests.exceptions import HTTPError
from pyTigerGraph import TigerGraphConnection


# Suppress all pyTigerGraph logs
logging.getLogger("pyTigerGraph").setLevel(logging.WARNING)
#
# Import Database configuration parameters from .env file
#
from mcp_server.config import tigerGraphConstants, set_Constents, TG_SYSTEM
HOST, GRAPH, USER, PASSWORD, SECRET, TOKEN = tigerGraphConstants()

class TigerGraph_Session():
    """
    The TigerGraph Session initialization performs the following checks:
    1. Determines if the database is running (ping)
    2. Determines if the specified graph in the .env file exists, if not, it will create a graph
    3. Checks to see if there is a Secret registered by the db user name and graph name, if there
       is no Secret, the system will create a secret and token and write it out to your .env file
    4. Once the session is authenticated it will set a TigerGraph Connection
    """
    def __init__(self):
        self.username = USER
        self.password = PASSWORD
        self.graphName = GRAPH
        self._secret = SECRET
        self._token = TOKEN

        try:
            self.conn = TigerGraphConnection(
                host=HOST,
                graphname=GRAPH,
                apiToken=TOKEN,
                username=USER,
                password=PASSWORD
            )
            results = self.getConnection().ping()
            if (results['error'] is not True):
                if(self.getConnection().check_exist_graphs(self.graphName) == False):
                    self._createGraph()    
                else:
                    self.secretsExists()

        except HTTPError as error:
            if error.response.status_code == 401:
                raise ConnectionError(">>> ERROR - Invalid credentials, please check your TigerGraph username / password.")
            
            raise ConnectionError(f">>> ERROR - TigerGraph server not running, {error}: ")

        except Exception as error:
             print(f">>> ERROR - TigerGraph server not running, {error}: ",file=sys.stderr)

   
    def getConnection(self) -> TigerGraphConnection:
        return self.conn
        
    def getSecretAlias(self) -> str:
        return f"{self.username}_{self.graphName}"

    #
    # This is a internal function that is called as part of the initialization process
    # If there is no Graph, create one and assign secrect and token to user.
    #
    def _createGraph(self) -> bool:
        resultSet = {}
        resultSet = self.getConnection().gsql("CREATE GRAPH "+ self.graphName + "(*)")
        print(resultSet)
        if isinstance(resultSet,str):
            if (resultSet.find("created") >=0):
                self._secret = ''
                self._token = ''
                self.secretsExists()
            else:
                return False
        return True
    #
    # Resolve the issue that testing to see if Secret Exists only when
    # creating a new Graph.  This function now allow testing when a graph 
    # already exists.
    #
    def secretsExists(self):
        results = self.getConnection().getSecrets()
        if (results.get(self.getSecretAlias(),None) is None):
            self._createSecret(self.getSecretAlias())
        else:
            print(f"TigerGraph Secret Already Exits for Alias: {self.getSecretAlias()}")


    #
    # Create a Secret and Token for secure connection
    #   
    def _createSecret(self, aliasName, expirationDate=2592000) -> bool:
        update_Flag = False
        self._token = ""
        try:
            #
            # Create a Secret, assign it an alias name
            #                     
            if (len(aliasName) > 0):
                    self._secret = self.getConnection().createSecret(alias=aliasName)
                    update_Flag=True
                    self._token = ""
                    #print("Secret =",self._secret)
            #
            # Create a token with default of 30 day expiration
            #            
            if (self._secret is not None):
                tokenTuple = self.getConnection().getToken('',lifetime=int(expirationDate))
                update_Flag=True
                self._token = tokenTuple[0]
                self.getConnection().apiToken = self._token
                #print("New Token =", tokenTuple)
            else:
                self.getConnection().apiToken = self._token
        
            # 
            # Update configuration .env file
            #
            if (update_Flag == True):
                set_Constents('secret',self._secret, TG_SYSTEM)
                set_Constents('token',self._token, TG_SYSTEM)
                        

        except LookupError as error:
            print("Error:",repr(error),file=sys.stderr)
            return False

        except Exception as error:
            print("createSecret/Token Error:",repr(error),file=sys.stderr)
            #traceback.print_exc()
            return False

        return True    
