import os, argparse
from smolagents import CodeAgent, ToolCallingAgent
from smolagents.models import AzureOpenAIServerModel
from smolagents.tools import ToolCollection
# from smolagents.templates import PromptTemplates
from mcp import StdioServerParameters
from smolagents.utils import AgentGenerationError
import time

def main():
    parser = argparse.ArgumentParser(description="Run an AI agent query using smolagents.")
    parser.add_argument("query", help="The prompt/query to run", nargs="+")
    args = parser.parse_args()

    query = " ".join(args.query)

    model = AzureOpenAIServerModel(
        model_id="gpt-4",
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version="2025-01-01-preview"
    )


    # model = HfApiModel(
    #     model_id="Qwen/Qwen2.5-Coder-32B-Instruct"
    # )
    
    server_params = StdioServerParameters(
        command="python",
        args=["MCP/server.py"],
        env={**os.environ}
    )
    
    with ToolCollection.from_mcp(server_params, trust_remote_code=True, structured_output=True) as tool_collection:
        # agent = CodeAgent(
        #     tools=tool_collection.tools, 
        #     model=model,
        #     # additional_authorized_imports=['json'],
        #     use_structured_outputs_internally= False,
        #     # code_block_tags="python",
        #     executor_type= "local"
        # )

        agent = ToolCallingAgent(
            tools=tool_collection.tools,
            model= model
        )
        
        # result = agent.run(query)
        for attempt in range(3):
            try:
                result = agent.run(query)
                break
            except AgentGenerationError:
                print("Rate limit")
                time.sleep(2)
        # print(result)

if __name__ == "__main__":
    main()
    