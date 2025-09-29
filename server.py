#Server.py
from fastmcp import FastMCP
from General_tools import General_ToolManager


mcp = FastMCP("Scifi_Agent")
General_tools = General_ToolManager()

@mcp.tool(name = "Google scholar search", enabled=True)
def Google_Scholar_search(topic: str, num_results: int = 5) -> list[dict]:
    """
    This tool queries Google Scholar via SerpAPI to return research papers. Always start Research papers query with this
    
    Args:
        topic: The search query for academic papers.
        num_results: Number of top papers to return.

    Returns:
            A list of dictionaries for each paper with:
            - title
            - abstract
            - authors (list of dicts with name)
            - year
            - venue
            - citationCount
            - url (main link)
    """
    return General_tools.google_scholar_search(topic, num_results)


@mcp.tool(name = "Semantic scholar search",enabled = False) 
def Semantic_Scholar_search(query:str = "", result_limit:int = 5) -> list[dict]:
    """
    This tool retrieves relevant research papers from Semantic Scholar based on a user-defined query.

    Args:
        query (str): The search query string, which can include keywords, author names, fields of study, publication venues, or other metadata.
        result_limit (int): The maximum number of papers to return (default is 5).

    Returns:
        A list of the top matching papers with rich metadata for each, including:
            - title
            - abstract
            - citation count
            - tldr (short summary if available)
            - fields of study
            - publication year
            - authors
            - open access status
            - direct link to PDF (if available)
            - paper URL
            - venue (conference or journal name)
        
    This tool is useful for literature reviews, sourcing papers for research, or finding up-to-date work on a specific topic.
    """

    return General_tools.semantic_scholar_search(query, result_limit)



@mcp.tool(name = "Wikipedia_search", enabled= True)
def wikipedia_search(topic:str) -> str:
    """
    This tool is used to acces the wikipedia search and Useful for retrieving general scientific concepts, background knowledge, and material property definitions.

    Args:
        topic(str): This is the topic string, for which the wikipedia api will retrieve relavent results for.

    Returns:
        The summary strings of the topic that was given at the input
    """
    return General_tools.wikipedia_tool.run(topic)


@mcp.tool(name = "Arxiv_search", enabled=True )
def arxiv_search(topic:str) -> str:
    """
    This tool is used to search and retrieve research papers from arxiv database. Use this when the user is fine with papers not being peer reviewed

    Args:
        topic(str): Takes in the topic for which the research papers are needed, format it such that the arxiv api understands it

    Returns:
        Provides all the meta data that we can get from th arxiv api
    """
    return General_tools.arxiv_tool.run(topic)

if __name__ == "__main__":
    mcp.run()
