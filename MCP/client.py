import os
from smolagents import CodeAgent
from smolagents.models import AzureOpenAIServerModel
from smolagents.tools import ToolCollection
from mcp import StdioServerParameters

def main():
    model = AzureOpenAIServerModel(
        model_id="gpt-4",
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version="2025-01-01-preview"
    )
    
    server_params = StdioServerParameters(
        command="python",
        args=["MCP/server.py"],
        env={**os.environ}
    )
    
    with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
        agent = CodeAgent(
            tools=tool_collection.tools, 
            model=model,
            additional_authorized_imports=['json']
            # system_prompt =
        )
        
        result = agent.run("In a thermodynamic system with 3 components and 2 phases, what is the number of degrees of freedom?")
        print(result)

if __name__ == "__main__":
    main()
    