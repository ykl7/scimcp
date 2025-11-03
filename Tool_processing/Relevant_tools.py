# Relevant_tools

import os,sys,json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastmcp import FastMCP
from openai import AzureOpenAI
from Tools.Mat_Sci_tools import MaterialScienceToolRegistry


client = AzureOpenAI(
    api_key= os.getenv("AZURE_API_KEY"),
    azure_endpoint= os.getenv("AZURE_ENDPOINT"),
    api_version= "2025-01-01-preview"
)

system_prompt = """
You are a tool selection assistant . 
Your job is to choose the most relevant tools from a given list of tool names and their descriptions 
based on a natural language query.

if any question is related to materials properties, always include the "Get Material Properties from MP" tool in the relevant tools.
ALWAYS INCLUDE WIKIPEDIA TOOL.REGARDLESS OF THE QUERY.
Always include the general tools such as Google scholar search, semantic scholar search, arxiv search/ar5iv search, if the question is related to scientific concepts, background knowledge, or academic papers.
### Input
- toolnames: A list of available tool names with short descriptions.
- query: A natural language request from the user.

### Task
- Analyze the query carefully.
- Select the 25 most relevant tools from the toolnames list.
- Return only the tool names, not explanations.

### Output
Return a JSON object in the following format:
{
  "Twentyfive_relevant_tools": ["tool1", "tool2", ..., "tool25"]
}
"""

def get_relevant(query, toolnames):
    try:
        response = client.chat.completions.create(
            model = "gpt-4o" ,  #"gpt-4" "gpt-5-mini"
            messages=[
                {"role":"system", "content": system_prompt},
                {"role":"user", "content": f"toolnames: {toolnames}\nQuery: {query}"}
            ],
            temperature=0
        )

        content =  response.choices[0].message.content
        output = json.loads(content)
        return output["Twentyfive_relevant_tools"]
    except Exception as e:
        return {"error": str(e)}
    

# if __name__ =="__main__":

#     toolnames = MaterialScienceToolRegistry.toolnames
#     relevant_tools = get_relevant(query = "An alloy system has 2 components and 1 phase. The ratio of α to β phases is 3:1. If the wt.% of element A is 40% in α and 20% in β, what is the total wt.% of A in the alloy?", toolnames = toolnames )
#     # output = json.load(rele)
#     print(relevant_tools)

