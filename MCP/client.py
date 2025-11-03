import os, argparse, time, sys
from smolagents import CodeAgent, ToolCallingAgent
from smolagents.models import AzureOpenAIServerModel, OpenAIServerModel
from smolagents.tools import ToolCollection
from mcp import StdioServerParameters
from smolagents.utils import AgentGenerationError
# from smolagents import Agent
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from smolagents import ToolCallingAgent, ActionStep, PlanningStep, FinalAnswerStep
from smolagents.agents import LogLevel
from openai import BadRequestError
# Setup Phoenix
register()
SmolagentsInstrumentor().instrument()


custom_instructions = """
IMPORTANT: When given a statement or claim about materials, technologies, or scientific facts:
1. Do NOT just assume the statement is true and explain how to implement it.
2. Instead, VERIFY the claim by:
   - Searching for supporting or contradicting evidence in research papers
   - Checking if the claim is theoretically sound based on material properties
   - Identifying any limitations, caveats, or conditions under which it's true
3. If you need a specific material property, always use the Material Project tools to look it up.
4. Provide a critical analysis:
   - Is the claim accurate? Partially accurate? Misleading?
   - What evidence supports or contradicts it?
   - Under what conditions is it valid?
   - What are the practical implications?
5. Refrain from looking for images as evidence; focus on textual and data-based verification.
6. Always cite sources and research findings to back up your verification.
7. ANSWER BEFORE EXCEEDING MAX STEPS.
"""

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Tool_processing.Relevant_tools import get_relevant
from Tools.Mat_Sci_tools import MaterialScienceToolRegistry

def main():
    parser = argparse.ArgumentParser(description="Run an AI agent query using smolagents.")
    parser.add_argument("query", help="The prompt/query to run", nargs="+")
    args = parser.parse_args()

    query = " ".join(args.query)

    toolnames = MaterialScienceToolRegistry.toolnames
    # relevant_tools = get_relevant(query = query, toolnames = toolnames)

    # if 
    model = AzureOpenAIServerModel(
        model_id="gpt-5-mini",  #"gpt-4" "gpt-5-mini" "gpt-4o"
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version="2024-12-01-preview" #"2025-01-01-preview" "2025-04-01-preview" "2024-12-01-preview"
    )

        # model = OpenAIServerModel(
        # model_id="gpt-4o",
        # api_base="https://api.openai.com/v1",
        # api_key=os.environ["OPENAI_API_KEY"],
        # )


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
        all_toolnames = [t.name for t in all_tools]

        relevant_tools = get_relevant(query=query, toolnames=all_toolnames)
        filtered_tools = [t for t in all_tools if t.name in relevant_tools]
        

        # agent = CodeAgent(
        #     tools=tool_collection.tools, 
        #     model=model,
        #     # additional_authorized_imports=['json'],
        #     use_structured_outputs_internally= False,
        #     # code_block_tags="python",
        #     executor_type= "local"
        # )
        # prompt_templates = smolagents.PromptTemplates(
        #     system_prompt="You must not answer the question directly. Always call a tool. If no tool is appropriate, say you cannot help."
        # )
        agent = ToolCallingAgent(
            tools=filtered_tools,
            model= model,
            # step_callbacks= step_callbacks,
            # instructions = custom_instructions,
            max_steps=20,
            planning_interval=2,
            # verbosity_level= LogLevel.DEBUG,
            # prompt_templates= prompt_templates,
        )
        # print("Registered tools:", list(agent.tools.keys()))
        # result = agent.run(query)
        result = None
        for attempt in range(3):
            try:
                result = agent.run(f"{query}\n\nIMPORTANT: Each question is provided multiple choices, based on the question, reason and choose the correct answer from the choices. This is MANDATORY.") #IMPORTANT: In your final answer, clearly state whether the initial claim is True or False based on your analysis. This is MANDATORY.
                break  #IMPORTANT: The final answer needs to be a simple one word answer to what the question is asking. This is MANDATORY.
            except AgentGenerationError as e:
                print(f"[Attempt {attempt+1}] AgentGenerationError: {str(e)}")
            except BadRequestError as e:
                if "content_filter" in str(e):
                    print(f"[Attempt {attempt+1}] Blocked by Azure Content Filter, modifying or softening prompt might help.")
                else:
                    print(f"[Attempt {attempt+1}] BadRequestError: {str(e)}")
            except Exception as e:
                print(f"[Attempt {attempt+1}] Unexpected error: {str(e)}")

            wait_time = 2 ** attempt
            print(f"Retrying in {wait_time} seconds...\n")
            time.sleep(wait_time)

        # if result is not None:
        #     print("Final Result:\n", result)
        # else:
        #     print("Agent failed after 3 attempts.")

if __name__ == "__main__":
    main()
    