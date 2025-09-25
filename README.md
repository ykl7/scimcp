# scimcp

### Current Repo status

Currently the repo contains research paper search and scraping agentic frame work. The primary tools used are powered by Semantic scholar and Serp api(Paid google scholar wrapper). Both the tools are connected via FastMCP to smolagent library wrapped LLM. Finally, the output includes, a complete information on meta data of requested domain research papers.

### Server.py

This is our tools hub. The tools are defined and hosted in mcp here. Currently the active tools are
- Google_Scholar_search
- Semantic_Scholar_search

Both the tools have their own function for filtering the get request data.

### Client.py

Here is where we define the LLM that makes use of the tools that are hosted on our defined mcp server in server.py. We are currently using:
- LLM model: Gpt-4
- Wrapper: smolagent
- LLM deployment: Azure

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


### Limitations

There is no chat.completion implemented yet, so it for now any query too llm is to enterd in the script



