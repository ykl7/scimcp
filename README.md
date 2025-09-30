# scimcp

### Current Repo status

Currently the repo contains Fastmcp powered agentic frame work for material science research. The repo contains two main category of tools, General tools(Google scholar, semantic scholar, arxiv and wikipedia) and 103 Material science tools. Both the tools are connected via FastMCP to smolagent library wrapped LLM. Finally, the output includes, a complete information on meta data of requested domain research papers.

### Server.py

This is where we register all our tools in the mcp server. Which in turn provides communications between tools and Client(LLM), the main two tool functions include
- general_tool_manager
- Mat_Sci_ToolManager

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

After that, Create a venv using ```uv venv``` , source it and then use ```uv sync``` to get all the dependencies from the clones repo

Furthermore, this repo needs you have following api_keys:
1) Semantic scholar api (https://www.semanticscholar.org/product/api#api-key)
2) Serp api (https://serpapi.com/users/sign_up)
3) Azure(optional)

### How to use
After setting up the environment, dependencies etc, please run following from ```scimcp```
```bash
python MCP/server.py
```
Now, to run the client, each general purpose tool gets prompted based on certain keywords.
```bash
# Google scholar (No special prompt required)
python MCP/client.py -- "Give me research papers on AI in material science"

#Semantic scholar
python MCP/client.py -- "Give me research papers on AI in material science, using semantic scholar"

#Arxiv 
python MCP/client.py -- "Give me research papers on AI in material science, no peer review needed"

#wikipedia (gets used for any general knowledge questions)
python MCP/client.py -- "What is a covalent bond"
```
### Limitations

- There is no chat.completion implemented yet, so for now any query to llm is to enterd in the cli
- ```Mat_Sci_tools.py``` are still havent completely been tested.



