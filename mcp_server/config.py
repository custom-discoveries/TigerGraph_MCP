#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# config.py: Manages environment variables by system specification
#******************************************************************************
import os
import sys
from dotenv import load_dotenv, find_dotenv, set_key

API = ""
HOST = ""
GRAPH = ""
USER = ""
PASSWORD = ""
SECRET = ""
TOKEN = ""
TOKENS = 0
OUTPUT_PATH=""
TG_SYSTEM = "tigerGraph"
ANTHROPIC = "ANTHROPIC"
GOOGLE = "GOOGLE"
OPENAI = "OPENAI"
LLM_MODEL_FAMILY=ANTHROPIC
MCP_SERVER_PATH="MCP_SERVER_PATH"

#
# Define .env keys specifically for TigerGraph 
#
tigerGraph_Keys:dict = {
    'host':"TG_HOST",
    'graph':"TG_GRAPH",
    'user':"TG_USERNAME",
    'password':"TG_PASSWORD",
    'secret':"TG_SECRET",
    'token':"TG_TOKEN",
    'outputPath':"TG_OUTPUT_DIR",
}
anthropic_Keys:dict = {
    'api_key':'ANTHROPIC_API_KEY',
    'llm':'ANTHROPIC_LLM_MODEL',
    'tokens':'ANTHROPIC_TOKENS'
}

openAI_Keys:dict = {
    'api_key':'OPENAI_API_KEY',
    'llm':'OPENAI_LLM_MODEL',
    'tokens':'OPENAI_TOKENS'
}

gemini_Keys:dict = {
    'api_key':'GOOGLE_API_KEY',
    'llm':'GOOGLE_LLM_MODEL',
    'tokens':'GOOGLE_TOKENS',
    'configPath':'JSON_CONFIG_PATH'    
}

MASTER_KEYS:dict = {
    TG_SYSTEM:tigerGraph_Keys,
    ANTHROPIC:anthropic_Keys,
    OPENAI:openAI_Keys,
    GOOGLE:gemini_Keys
}

def tigerGraphConstants(output=False):
    try:
        #
        # Load configuration attributes from .env file
        #
        load_dotenv(find_dotenv())
        if (TG_SYSTEM in MASTER_KEYS.keys()):
            system_keys = MASTER_KEYS[TG_SYSTEM]
        else:
            print(f"Error in initializeConstants: system parameter {TG_SYSTEM} not found", file=sys.stderr)
            raise LookupError("Error in initializeConstants: system parameter {system} not found")
        

        HOST = os.getenv(system_keys['host'],"http://localhost")
        GRAPH = os.getenv(system_keys['graph'],"My_Graph")
        USER = os.getenv(system_keys['user'],"itMeAgain")
        PASSWORD = os.getenv(system_keys['password'],"tryToGuess")
        SECRET = os.getenv(system_keys['secret'],'')
        TOKEN = os.getenv(system_keys['token'],'')
        OUTPUT_PATH = os.getenv(system_keys['outputPath'],'')
        if output:
            return OUTPUT_PATH
        else:
            return (HOST, GRAPH, USER, PASSWORD, SECRET, TOKEN)
        
    except Exception as error:
        print(f"Error in initializeConstants {error}", file=sys.stderr)
        raise LookupError(f"Error in tigerGraphConstants {error}")
    
def getMCPServerConfig():
        load_dotenv(find_dotenv())
        MCP_PATH = os.getenv('MCP_SERVER_PATH','')
        return MCP_PATH
        

def getDefaultSystem():
        load_dotenv(find_dotenv())
        LLM_MODEL_FAMILY = os.getenv('LLM_MODEL_FAMILY', ANTHROPIC)
        #print(f"Initilizing LLM to {LLM_MODEL_FAMILY}")
        return LLM_MODEL_FAMILY

def initialLLMConstants():
    try:
        #
        # Load configuration attributes from .env file
        #
        load_dotenv(find_dotenv())
        LLM_MODEL_FAMILY = getDefaultSystem()
         
        return (LLM_MODEL_FAMILY)

    except Exception as error:
        print(f"Error in initializeConstants {error}", file=sys.stderr)
        raise LookupError(f"Error in initializeConstants {error}")
    
def getALLFamilyLLMConstants():
    try:
        #
        # Load configuration attributes from .env file
        #
        load_dotenv(find_dotenv())
    
        if (LLM_MODEL_FAMILY in MASTER_KEYS.keys()):
            system_keys = MASTER_KEYS[LLM_MODEL_FAMILY]
        else:
            print(f"Error in initializeConstants: system parameter {LLM_MODEL_FAMILY} not found", file=sys.stderr)
            raise LookupError("Error in initializeConstants: system parameter {system} not found")
        
        TG_SYSTEM, ANTHROPIC, OPENAI, GOOGLE = MASTER_KEYS.keys()

        return ANTHROPIC, OPENAI, GOOGLE 

    except Exception as error:
        print(f"Error in initializeConstants {error}", file=sys.stderr)
        raise LookupError(f"Error in initializeConstants {error}")

def getLLMConstants(familyName:str):

    if (familyName in MASTER_KEYS.keys()):
        system_keys = MASTER_KEYS[familyName]
    else:
        print(f"Error in initializeConstants: system parameter {LLM_MODEL_FAMILY} not found", file=sys.stderr)
        raise LookupError(f"Error in initializeConstants: system parameter {LLM_MODEL_FAMILY} not found")

    API_KEY = os.getenv(system_keys['api_key'],'')
    LLM_MODEL = os.getenv(system_keys['llm'],'')
    TOKENS = os.getenv(system_keys['tokens'],0)
    #JSON_CONFIG_PATH = os.getenv(system_keys['configPath'],"")

    return (API_KEY, LLM_MODEL, int(TOKENS))

def set_Constents(key:str, value, system):
    
    system_keys = MASTER_KEYS[system]
    #
    # Check key is in system list
    #
    if (key in system_keys.keys()):
        set_key(find_dotenv(),system_keys[key], value, export=False)

