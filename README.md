# TigerGraph-MCP

Custom Discoveries TigerGraph-MCP V2.1 is a community based python Model Context Protocol server that exposes TigerGraph operations (queries, schema, vertices, edges, UDFs) as structured tools, prompts, and URI-based resources for MCP agents. This will allow you to interact with your TigerGraph Database using natural 
language commands!

## Table of Contents

1. [Requirements](#requirements)
2. [Features](#features)  
3. [Project Structure](#project-structure)  
4. [Installation](#installation)  
5. [Configuration](#configuration-setup)
6. [Running Chat Bot](#running-chat-bot)
7. [Connecting to Claude Desktop](#connecting-to-claude-desktop)
8. [Contributing](#contributing)  
9. [License](#license)  
10. [Releases](#Releases)
    
## Requirements

 - You will need to run **TigerGraph Version >= 4.2.0**, either in the cloud or in a Docker Image.
 - Make sure to add a TigerGraph dba user and set your password.  Set role to: 'superuser'.
 - Setup local environment with Python >= 3.12 (run the installUVEnvironment.sh script)

## Features

- **Schema Introspection**  
  Retrieve full graph schema (vertex & edge types).

- **Query View**
  Retrieve list of available queires that your able to run

- **Query Execution**  
  Run installed GSQL queries or raw GSQL strings with parameters.

- **Creation Vertex & Edge**
  Create Vertices and Edges programmatically

- **Alter Vertex**
  Allows for altering the Vertex to include support for Vector attributes

- **Upsert Vertex & Edge**  
  Update vertices and edges attributes programmatically (this includes Vector attributes).

- **UDF & Algorithm Listing**  
  Fetch installed user-defined functions and GDS algorithm catalogs.

## Features++ (Kick-Ass Features include)
  1. We are including a mcp_chatbot that allow you "chat" with the database. You will need to configure
     two files.  First, you will need to configure the mcp_server/.env file with the LLM you want to use
     (default is Anthropic LLM model) Second, you will need to configure the server_config.json file,
      under mcp_server/mcp_chatbot folder, specifying the full path to the main.py file. 
      The chatbot usage is as follows:
       - @listQueries to see available Query Output Files
       - @<query_file_name> list content of Query file
       - /tools to list the available tools under the mcp server
       - /prompts to list the available prompts under the mcp server
       - /resources is a **planned future enhancment**
  
  2. Custom Discoveries TigerGraph-MCP V2.0 now includes enhanced functionality for exporting 
     query results to CSV or JSON file formats within a designated output directory. This output
     directory can be configured through the mcp_server/.env file, with the default location 
     set to ./Output.

  3. We have developed some Session Management Features that will help the developer with
  handling TigerGraph Session around SECRET & TOKEN Management.  In short, TigerGraph session 
  initialization checks the following:

    1. Determines if the database is running (ping)
    2. Determines if the specified graph in the .env file exists, if not, it will create a graph
    3. Checks to see if there is a Secret registered by the combination of db user name and graph name
       (i.e. Secret Alias), if there is no Secret Alias, the system will create a secret and token and
       write it out to your .env file
    4. Once the session is authenticated it will set a TigerGraph Connection

## Project Structure

```
TigerGraph-MCP/
├── installUVEnvironment.sh   # Intitalizes vitural environment if one exists, if not it will
                                create one, and load it with the project dependencies in the
                                requirements.txt file.
├── LICENSE                   # MIT License
├── main.py                   # MCP app bootstrap (`run_server()`) Used to start TigerGraph_MCP server
├── chatBot_Main.py           # Main python program to invoke mcp_chatbot.py
├── mcp_server
      ├── .env                # TigerGraph (HOST, GRAPH, SECRET) & LLM configuration paramaters
      ├── config.py           # Reads environment config file (.env) and defines System Constants
      ├── mcp_chatbot
            ├── mcp_chatbot.py     # Chatbot for LLM to interact with TigerGraph MCP Server (uses .env file)
            ├── server_config.json # Configuration file to define TigerGraph MCP Server
      ├── tigerGraph
            ├── interface.py      # Interface definitions of client methods
            ├── mcp_Server.py     # `@mcp.tool` and `@mcp.prompts` definitions, exposing client methods & prompts
            ├── prettyPrintDir.py # Implements pretty print directory functionality
            ├── services.py       # Implement service calls to TigerGraph database
            ├── session.py        # Encapsulates TigerGraphConnection and core session operations
       
├── Output                    # Output directory where Query outputs are written (.csv or .json format)       
├── pyproject.toml            # Project metadata & dependencies
├── README.md                 # This markdown README file
├── requirements.txt          # Python package dependencies
├── runChatBot.sh             # Unix shell script to run TigerGraph ChatBot 
└── .gitignore                # Github/OS/Python ignore rules
```

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/customdiscoveries/TigerGraph_MCP.git
   cd TigerGraph-MCP
   ```
2. **Copy Example Configuration files**
   ```bash
   cp mcp_server/.env-example .env
   cp mcp_server/mcp_chatbot/example-server_config.json server_config.json
   ```
3. **Create, Install Dependencies & Activate a virtual environment**  
   ```bash
   installUVEnvironment.sh
   ```

## Configuration Setup

**MCP TigerGraph Server**

The assumption is that the developer has a instance of TigerGraph 
running either in the cloud or on a Linux Desktop. Furthermore, it
is assumed that the TigerGraph instance has a defined dba user 
(with valid roles and password).

Please edit your .env configuration (that you copied from the .env-exmaple) file 
with the following required attributes to create a TigerGraph session:

- TG_HOST=http://localhost
- TG_GRAPH=tigerGraph_Graph_name
- TG_USERNAME=tigerGraph_dba_user_name
- TG_PASSWORD=tigerGraph_dba_user_password
- TG_SECRET=(automatically captured if you don't provide one)
- TG_TOKEN=(automatically captured if you don't provide one)

**TigerGraph MCP ChatBot**

The MCP ChatBot currently supports two LLMs, OPEN AI, an Anthropic claude. 

1. You will need to modify the .env (same as used in the mcp server) configuration 
file and set the LLM_MODEL_FAMILY attribute. 

- LLM_MODEL_FAMILY='ANTHROPIC' # Currently supports: 'ANTHROPIC' or 'OPENAI'
  #
- ANTHROPIC_LLM_MODEL='claude-3-7-sonnet-20250219'
- ANTHROPIC_API_KEY="Your Anthropic Key goes here"
- ANTHROPIC_TOKENS=2024
  #
- OPENAI_LLM_MODEL='gpt-4.1-mini'
- OPENAI_TOKENS=2024
- OPENAI_API_KEY="Your Open AI Key goes here"

2. You will need to update the server_config.json file (that you made a copy of) and
   edit the path to the run command with your full path name:
   
     "args": ["run", "/**Your full path goes here**/MCP-Repository/TigerGraph-MCP/main.py"]

## Running Chat Bot

Once you have completed all of your configuration setup. It is now time to see the fruit of your labor!
To run the Chat Bot simply invoke the script runChatBot.sh

```bash
. runChatBot.sh
```
You should see a Welcome Banner:
```
Welcome to Custom Discoveries TigerGraph MCP Chatbot!
Type your queries or type ['quit'|'exit'] to exit.
Use /tools to list available tools
Use /prompts to list available prompts

Query:
```
At the Query prompt type /tools to get a list of avaialbe tools to interactive with TigerGraph Graph database.

## Connecting to Claude Desktop

This MCP server can be installed into the **Claude Desktop** client so that Claude can invoke your TigerGraph tools directly:
See link for setting up **Claude Desktop** at: https://modelcontextprotocol.io/quickstart/user#2-add-the-filesystem-mcp-server

Modify the configuration file at:

- macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
- Windows: %APPDATA%\Claude\claude_desktop_config.json
After configuring claude_desktop_config.json file, restart Claude Desktop and you’ll see your MCP tools available via the hammer 🛠 icon.


## Contributing

1. Fork the repository  
2. Create a feature branch  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes  
   ```bash
   git commit -m "Add YourFeature"
   ```
4. Push to branch  
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a Pull Request  

Please ensure all new code is covered by tests and follows PEP-8 style.

## License

This project is licensed under the **MIT License**.

## Releases

**V2.1** is the latest release that can be found at: https://github.com/custom-discoveries/TigerGraph_MCP/releases/tag/V2.1
