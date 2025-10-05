import os, argparse, time, sys
from smolagents import CodeAgent, ToolCallingAgent
from smolagents.models import AzureOpenAIServerModel
from smolagents.tools import ToolCollection
from mcp import StdioServerParameters
from smolagents.utils import AgentGenerationError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Tool_processing.Relevant_tools import get_relevant
from Tools.Mat_Sci_tools import MaterialScienceToolRegistry

def main():
    parser = argparse.ArgumentParser(description="Run an AI agent query using smolagents.")
    parser.add_argument("query", help="The prompt/query to run", nargs="+")
    args = parser.parse_args()

    query = " ".join(args.query)

    toolnames = MaterialScienceToolRegistry.toolnames
    relevant_tools = get_relevant(query = query, toolnames = toolnames)

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
        all_tools = tool_collection.tools
        filtered_tools = [t for t in all_tools if t.name in relevant_tools]
        

        # agent = CodeAgent(
        #     tools=tool_collection.tools, 
        #     model=model,
        #     # additional_authorized_imports=['json'],
        #     use_structured_outputs_internally= False,
        #     # code_block_tags="python",
        #     executor_type= "local"
        # )

        agent = ToolCallingAgent(
            tools=filtered_tools,
            model= model
        )
        
        # result = agent.run(query)
        for attempt in range(3):
            try:
                result = agent.run(query)
                # print(result)
                break
            except AgentGenerationError:
                print("Rate limit")
                time.sleep(2)


if __name__ == "__main__":
    main()
    