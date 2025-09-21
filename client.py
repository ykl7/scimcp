import os
from smolagents import CodeAgent, InferenceClientModel
from smolagents.models import AzureOpenAIServerModel
from smolagents.tools import ToolCollection
from mcp import StdioServerParameters
import asyncio

def sync_agent_run():

    model = AzureOpenAIServerModel(
        model_id="gpt-4",
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key = os.getenv("AZURE_API_KEY"),
        api_version="2025-01-01-preview"
    )
    #model = InferenceClientModel() Please uncomment this, im using Azure as i run outof free tokens on inference

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={**os.environ}
    )

    with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tool_collection:
        agent = CodeAgent(tools=tool_collection.tools, model=model)
        return agent.run("What's the weather in Stony Brook right now?")

async def main():
    result = await asyncio.to_thread(sync_agent_run)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
