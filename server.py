from fastmcp import FastMCP
from langchain.tools import Tool
from semanticscholar import SemanticScholar
from langchain_community.utilities.google_scholar import GoogleScholarAPIWrapper
from langchain_community.tools.google_scholar import GoogleScholarQueryRun
from typing import List, Dict
import os
import requests

mcp = FastMCP("Weather_agent")

# def google_scholar_search():
#     google_scholar_search = GoogleScholarQueryRun(api_wrapper=GoogleScholarAPIWrapper(serp_api_key=os.environ["SERP_API_KEY"]))
#     return google_scholar_search

# tool = Tool(
#     name="Google Scholar Search",
#     func=google_scholar_search().run,
#     description="Useful for searching academic papers and articles on Google Scholar."
# )


def extract_google_scholar_papers(data: dict):
    papers = []
    for result in data.get("organic_results", []):
        title = result.get("title", "N/A")
        link = result.get("link", "N/A")
        snippet = result.get("snippet", "N/A")

        authors_list = result.get("publication_info", {}).get("authors", [])
        authors = ", ".join([author.get("name", "") for author in authors_list])
        resources = result.get("resources", [])
        venue = resources[0].get("title") if resources else "N/A"
        cited = result.get("inline_links", {}).get("cited_by", {}).get("total", "")
        summary = result.get("publication_info", {}).get("summary", "")
        year = "N/A"
        for token in summary.split():
            if token.isdigit() and len(token) == 4:   # Just getting the year
                year = token
                break

        papers.append({
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": snippet,
            "venue": venue,
            "cited_by": cited,
            "link": link
        })

    return papers

# @mcp.tool
# def Google_scholar_search(topic:str) -> str:
#     """
#     This function is used for searching academic papers and articles on Google scholar
#     Args:
#          Topic for which the api should search the papers on, this can also include author and domain specifications
#     Output:
#          Returns the top matching papers with metadata such as abstract, title, authors, publication year, and link.
#     """
#     return tool.run(topic)


@mcp.tool
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
    params = {
        "engine": "google_scholar",
        "q": topic,
        "num": num_results,
        "api_key": os.environ["SERP_API_KEY"]
    }

    response = requests.get("https://serpapi.com/search", params=params)
    response.raise_for_status()

    data = response.json()
    filtered_metadata = extract_google_scholar_papers(data)

    return filtered_metadata


@mcp.tool
def Semantic_Scholar_search(query="", result_limit=5) -> list[dict]:
    """
    This tool retrieves relevant research papers from Semantic Scholar based on a user-defined query.

    Args:
        query (str): The search query string, which can include keywords, author names, fields of study, publication venues, or other metadata.
        result_limit (int): The maximum number of papers to return (default is 5).

    Output:
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
    # api_key = os.environ["SEMANTIC_SCHOLAR_API"]
    fields = "title,abstract,citationCount,tldr,fieldsOfStudy,year,authors,isOpenAccess,openAccessPdf,url,venue"

    rsp = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
                           headers={'X-API-KEY': "aBwBbmCpic50CTnKIAXYCuDAIJiUoQaaEbKhsQye"},
                           params={'query': query, 'limit': result_limit, 'fields': fields})

    rsp.raise_for_status()
    results = rsp.json()

    return results.get("data", [])


if __name__ == "__main__":
    mcp.run()
