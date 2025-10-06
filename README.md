# scimcp

### Current Repo status

Currently the repo contains Fastmcp powered agentic frame work for material science research. The repo contains two main category of tools, General tools(Google scholar, semantic scholar, arxiv and wikipedia) and 103 Material science tools. Both the tools are connected via FastMCP to smolagent library wrapped LLM. Finally, the output includes, a complete information on meta data of requested domain research papers and questions.

### Server.py

This is where we register all our tools in the mcp server. Which in turn provides communications between tools and Client(LLM), the main two tool functions include
- general_tool_manager
- Mat_Sci_ToolManager
- mp_manager (MaterialsProject tool)

Both the functions have their category specific tools which the model can use

### Client.py

Here is where we define the LLM that makes use of the tools that are hosted on our defined mcp server in server.py. We are currently using:
- LLM model: Gpt-4
- Wrapper: smolagent
- LLM deployment: Azure

### Tools

We have two category of tools, ```General_tools.py``` and ```Mat_Sci_tools.py```, which are called on by the server,py
### Requirements

Clone the repo and use uv for creating environments, handling dependencies etc. Dont use conda and pip.

Before all install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Go through this documentation for more details https://docs.astral.sh/uv/getting-started/installation/

After that, Create a venv using ```uv venv``` , source it and then use ```uv sync``` to get all the dependencies from the cloned repo

Furthermore, this repo needs you have following api_keys:
1) Semantic scholar api (https://www.semanticscholar.org/product/api#api-key)
2) Serp api (https://serpapi.com/users/sign_up)
3) Azure(optional)

### How to use
After setting up the environment, dependencies etc, please run following from ```scimcp```
```bash
python MCP/server.py
```
This starts the FastMCP server, now in **another terminal** we access the server tools from client.py.
To run the client, each general purpose tool gets prompted based on certain keywords.

Below are few examples on how to trigger required tools
```bash
# Google scholar (No special prompt required)
python MCP/client.py -- "Give me research papers on AI in material science"

#Semantic scholar
python MCP/client.py -- "Give me research papers on AI in material science, using semantic scholar"

#Arxiv 
python MCP/client.py -- "Give me research papers on AI in material science, no peer review needed"

#wikipedia (gets used for any general knowledge questions)
python MCP/client.py -- "What is a covalent bond"

#Mat_Sci_Tools (Tools change based on the calculations)
python MCP/client.py -- "An alloy system has 2 components and 1 phase. The ratio of α to β phases is 3:1. If the wt.% of element A is 40% in α and 20% in β, what is the total wt.% of A in the alloy?"

#Material_Project_tool (if no specific properties are asked, dafault properties(4) are used)
python MCP/client.py -- "Give me properties of NaCl"
```
### Limitations

- There is no chat.completion implemented yet, so for now any query to llm is to enterd in the cli
- No option to download or saved the retrieved information 



