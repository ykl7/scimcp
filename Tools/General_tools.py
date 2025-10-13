# General_tools.py

import os, requests,sys
from langchain.tools import Tool
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_community.agent_toolkits.load_tools import load_tools
from typing import List, Dict, Any
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Tools.ar5iv_arxiv_search import ar5iv_search

class General_Tools:
    def __init__(self):
        self.wikipedia_tool = self._load_wikipedia_tool()
        self.arxiv_tool = self._load_arxiv_tool()

    def _load_wikipedia_tool(self):
        wrapper = WikipediaAPIWrapper(top_k_results=5)
        wiki = WikipediaQueryRun(api_wrapper=wrapper)
        return Tool(
            name="Wikipedia Search",
            func=wiki.run,
            description="Get summaries of scientific concepts or background knowledge from Wikipedia."
        )

    def _load_arxiv_tool(self):
        wrapper = ArxivAPIWrapper(top_k_results=5, load_all_available_meta=True,)
        arxiv = ArxivQueryRun(api_wrapper=  wrapper)
        return Tool(
            name="Arxiv Search",
            func=arxiv.run,
            description="Search academic papers on arXiv."
        )

    def google_scholar_search_tool(self, topic: str, num_results: int = 5) -> List[Dict[str, Any]]:
        params = {
            "engine": "google_scholar",
            "q": topic,
            "num": num_results,
            "api_key": os.environ["SERP_API_KEY"]
        }
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        return self._extract_google_scholar_papers(response.json())

    def semantic_scholar_search_tool(self, query: str, result_limit: int = 5) -> List[Dict[str, Any]]:
        fields = "title,abstract,citationCount,tldr,fieldsOfStudy,year,authors,isOpenAccess,openAccessPdf,url,venue"
        response = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            headers={'X-API-KEY': os.environ["SEMANTIC_SCHOLAR_API"]},
            params={'query': query, 'limit': result_limit, 'fields': fields}
        )
        response.raise_for_status()
        return self._extract_semantic_scholar_papers(response.json().get("data", []))

    def _extract_google_scholar_papers(self, data: dict) -> List[Dict[str, Any]]:
        papers = []
        for result in data.get("organic_results", []):
            title = result.get("title", "N/A")
            link = result.get("link", "N/A")
            snippet = result.get("snippet", "N/A")
            authors_list = result.get("publication_info", {}).get("authors", [])
            authors = ", ".join([a.get("name", "") for a in authors_list])
            resources = result.get("resources", [])
            venue = resources[0].get("title") if resources else "N/A"
            cited = result.get("inline_links", {}).get("cited_by", {}).get("total", "")
            summary = result.get("publication_info", {}).get("summary", "")
            year = next((t for t in summary.split() if t.isdigit() and len(t) == 4), "N/A")

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

    def _extract_semantic_scholar_papers(self, results: list[dict]) -> List[Dict[str, Any]]:
        papers = []
        for result in results:
            title = result.get("title", "N/A")
            link = result.get("url", "N/A")
            year = result.get("year", "N/A")
            venue = result.get("venue", "N/A")
            cited = result.get("citationCount", 0)
            abstract = result.get("abstract", "No abstract available.")
            authors = ", ".join([a.get("name", "") for a in result.get("authors", [])])
            pdf_url = result.get("openAccessPdf", {}).get("url", None)

            papers.append({
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract.strip() if abstract else "No abstract available",
                "venue": venue,
                "cited_by": cited,
                "link": link,
                "pdf_url": pdf_url
            })
        return papers

_general_tools = General_Tools()


def general_tools_manager(mcp):
    """Register all research-related tools"""
    
    @mcp.tool(name="Google scholar search", enabled=False)  # Disabled by default due to API costs
    def google_scholar_search(topic: str, num_results: int = 5) -> list[dict]:
        """
        This tool queries Google Scholar via SerpAPI to return research papers. Always start Research papers query with this unless explicitly mentioned.
        
        Args:
            topic: The search query for academic papers.
            num_results: Number of top papers to return.

        Returns:
            Provides all the meta data and their information that the api provides, but always include abstract if available!
        """
        return _general_tools.google_scholar_search_tool(topic, num_results)

    @mcp.tool(name="Semantic scholar search", enabled=True) 
    def semantic_scholar_search(query: str = "", result_limit: int = 5) -> list[dict]:
        """
        This tool retrieves relevant research papers from Semantic Scholar based on a user-defined query.It always include abstractin output, if its available
        Args:
            query (str): The search query string, which can include keywords, author names, fields of study, publication venues, or other metadata.
            result_limit (int): The maximum number of papers to return (default is 5).

        Returns:
            Provides all the meta data and their information that the api provides, but always include abstract if available!
        """
        return _general_tools.semantic_scholar_search_tool(query, result_limit)

    @mcp.tool(name="Arxiv search", enabled=True)
    def arxiv_search(topic: str) -> str:
        """
        This tool is used to search and retrieve research papers from arxiv database. Use this when the user is fine with papers not being peer reviewed

        Args:
            topic(str): Takes in the topic for which the research papers are needed, format it such that the arxiv api understands it

        Returns:
            Provides all the meta data that we can get from the arxiv api
        """
        return _general_tools.arxiv_tool.run(topic)
    
    @mcp.tool(name="Ar5iv search", enabled=True)
    def ar5iv_search_tool(query: str, top_k: int = 5)-> list[dict]:
        
        """
        This tool is used to search and retrieve research papers from ar5iv database, which has better formatting than arxiv. Use this when the user is fine with papers not being peer reviewed and want full text of paper.
        The output MUST include abstract and FULL TEXT, with a summary section wise if available. Do not wait for user to ask for full text, provide it in the first go if available.
        Args:
            query(str): Takes in the topic for which the research papers are needed, format it such that the ar5iv api understands it
            top_k(int): Number of top results to return (default is 5)

        Returns:
            - Title
            - Authors
            - Abstract
            - Full text (section wise if available) COMPULSORY if available
        """
        return ar5iv_search(query, top_k)
    
    @mcp.tool(name="Wikipedia search", enabled=True)
    def wikipedia_search(topic: str) -> str:
        """
        This tool is used to acces the wikipedia search and Useful for retrieving general scientific concepts, background knowledge, and material property definitions.

        Args:
            topic(str): This is the topic string, for which the wikipedia api will retrieve relavent results for.

        Returns:
            The summary strings of the topic that was given at the input
        """
        return _general_tools.wikipedia_tool.run(topic)
