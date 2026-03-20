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
import anthropic
import argparse
# Setup Phoenix
register()
SmolagentsInstrumentor().instrument()


custom_instructions = """
You are a materials science expert assistant.

MANDATORY TOOL USAGE RULES:
1. For material properties (band gap, density, crystal structure, etc.) -> MUST use Materials Project tools
2. For formulas, equations, or calculations -> MUST search for verification using paper/Wikipedia tools  
3. For scientific definitions or fundamental concepts -> MUST use Wikipedia
4. For claims requiring evidence or citations -> MUST use Semantic Scholar, ArXiv, or Ar5iv tools
5. For research findings or experimental data -> MUST search literature for verification

You MAY use your knowledge for:
- Basic logical reasoning and deduction
- Comparing and synthesizing information from tool results
- Drawing conclusions from verified data

When given a statement or claim:
1. Do NOT assume it's true - VERIFY using tools
2. Search for supporting or contradicting evidence in research papers
3. Check material properties using Materials Project when relevant
4. Identify limitations, caveats, or conditions for validity
5. Provide critical analysis with evidence from tools

IMPORTANT: 
- Refrain from looking for images as evidence; focus on textual and data-based verification
- Always cite sources and research findings from tool results
- ANSWER BEFORE EXCEEDING MAX STEPS
"""

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Tool_processing.Relevant_tools import get_relevant
from Tools.Mat_Sci_tools import MaterialScienceToolRegistry

def main():
    parser = argparse.ArgumentParser(description="Run an AI agent query using smolagents.")
    parser.add_argument("query", help="The prompt/query to run", nargs="+")
    parser.add_argument("--prov", choices=["azure", "openai", "anthropic"], default="openai", help="Which prov to use for the agent.")
    parser.add_argument("--model", help = "Name of the model from the provider, e.g. gpt-5-mini for Azure or OpenAI, claude-2 for Anthropic")
    
    args = parser.parse_args()

    query = " ".join(args.query)
    model_name = args.model if args.model else "gpt-5-mini"  # Default to gpt-5-mini if not specified
    toolnames = MaterialScienceToolRegistry.toolnames
    # relevant_tools = get_relevant(query = query, toolnames = toolnames)

    if args.prov == "azure":
        # Model 1: Azure GPT-5-mini
        model = AzureOpenAIServerModel(
            model_id=model_name,
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2024-06-01")
        )
    elif args.prov == "openai":
        # Model 2: OpenAI GPT-5-mini
        model = OpenAIServerModel(
            model_id=model_name,
            api_key = os.getenv("OPENAI_API_KEY"))
    elif args.prov == "anthropic":
        # Model 3: Anthropic Claude-2
        model = anthropic.Anthropic(
            model_id=model_name,
            api_key=os.getenv("ANTHROPIC_API_KEY"))

        
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
        
        print(f"\n Filtered to {len(filtered_tools)} relevant tools: {[t.name for t in filtered_tools]}\n")

        # ========================================
        # CodeAgent: Best for structured data tools
        # ========================================
        agent = CodeAgent(
            tools=filtered_tools,
            model=model,
            additional_authorized_imports=['json', 're', 'math'],
            # instructions=custom_instructions,
            planning_interval=2,
            use_structured_outputs_internally=False,
            max_steps=15,
        )
        
        # ========================================
        # ToolCallingAgent: Use only if tools return simple text
        # ========================================
        # agent = ToolCallingAgent(
        #     tools=filtered_tools,
        #     model=model,
        #     max_steps=20,
        #     planning_interval=2,
        #     # instructions=custom_instructions,  # Too complex for weaker models
        # )
        # print("Registered tools:", list(agent.tools.keys()))
        # result = agent.run(query)
        result = None
        for attempt in range(3):
            try:
                result = agent.run(f"{query}\n\n IMPORTANT: In your final answer, clearly state whether the initial claim is True or False based on your analysis. This is MANDATORY.") #IMPORTANT: In your final answer, clearly state whether the initial claim is True or False based on your analysis. This is MANDATORY.
                break  #IMPORTANT: Each question is provided multiple choices, based on the question, reason and choose the correct answer from the choices. This is MANDATORY.
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
    # parser = argparse.ArgumentParser(description="Run an AI agent query using smolagents.")
    main()
    