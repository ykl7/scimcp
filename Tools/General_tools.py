# General_tools.py

import os, requests,sys,re
from itertools import islice
from langchain_core.tools import Tool
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
    
    def _sanitize_query(self, query: str, max_keywords: int = 5) -> str:
        """
        Simplifies complex keyword dumps from LLMs into shorter queries.
        Keeps only relevant keywords (alphanumeric words).
        """
        # Clean query and extract keywords
        keywords = re.findall(r"\b[a-zA-Z0-9_+\-\.]+\b", query)
        short_query = " ".join(islice(keywords, max_keywords))
        return short_query
    
    def _load_wikipedia_tool(self):
        wrapper = WikipediaAPIWrapper(top_k_results=5)
        wiki = WikipediaQueryRun(api_wrapper=wrapper)
        return Tool(
            name="Wikipedia Search",
            func=wiki.run,
            description="Get summaries of scientific concepts or background knowledge from Wikipedia."
        )

    def _load_arxiv_tool(self):
        wrapper = ArxivAPIWrapper(top_k_results=5, load_all_available_meta=True)
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
        query = self._sanitize_query(query)
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
    
    @mcp.tool(name="Google Scholar Search", enabled=False)
    def google_scholar_search(topic: str, num_results: int = 5) -> list[dict]:
        """
        Search for academic papers using Google Scholar via SerpAPI.
        
        Best for: Broad academic searches with high-quality citation metrics.
        
        Returns: Paper metadata including title, authors, year, abstract, venue, 
        citation count, and links.
        
        Args:
            topic: Search query (keywords, author names, or specific topics)
            num_results: Number of papers to return (default: 5)
            
        Note: This tool is disabled by default due to API costs.
        """
        return _general_tools.google_scholar_search_tool(topic, num_results)

    @mcp.tool(name="Semantic Scholar Search", enabled=False)
    def semantic_scholar_search(query: str = "", result_limit: int = 5) -> list[dict]:
        """
        Search for research papers from Semantic Scholar API.
        
        Best for: Quick metadata lookups when you need paper details before 
        retrieving full text. Provides clean structured data.
        
        Returns: Paper metadata including title, authors, abstract, citation count, 
        year, venue, link, and PDF URL if open access.
        
        Args:
            query: Search query (keywords, author names, or topics)
            result_limit: Maximum number of papers to return (default: 5)
            
        Note: This tool is disabled by default.
        """
        return _general_tools.semantic_scholar_search_tool(query, result_limit)

    @mcp.tool(name="ArXiv Search", enabled=True)
    def arxiv_search(topic: str) -> str:
        """
        Search for research papers on arXiv.
        
        Best for: Computer science, physics, mathematics, and related fields. 
        Provides abstracts and metadata, useful for initial paper discovery.
        
        Returns: Paper metadata including title, authors, abstract, publication date, 
        and links.
        
        Args:
            topic: Search query formatted as a natural sentence or specific paper/author 
            name (e.g., "machine learning transformers" or "attention is all you need")
        """
        return _general_tools.arxiv_tool.run(topic)
    
    @mcp.tool(name="Ar5iv Search", enabled=True)
    def ar5iv_search_tool(query: str, top_k: int = 3) -> list[dict]:
        """
        Search and retrieve full-text research papers from ar5iv database.
        If paper id is known, set top_k=1 for direct retrieval.
        
        Best for: Accessing complete paper content with better formatting than arXiv. 
        Use after finding relevant papers with other search tools.
        
        Returns: Comprehensive paper data including title, authors, abstract, and 
        full text organized by sections.
        
        Args:
            query: Search query formatted as a natural sentence or specific paper/author 
            name (e.g., "transformer architecture" or "Vaswani et al")
            top_k: Number of top results to return.
            
            IMPORTANT - When to set top_k:
            - top_k=1: ONLY if you have a specific arXiv ID or exact paper title
              Example: query="2404.12345" or query="Attention is All You Need"
            - top_k=3 (default): For topic-based searches (use this most of the time)
              Example: query="transformer attention mechanisms"
            - top_k>3: Rarely needed; avoid unless specifically requested by user
            
        Important: Only call this tool after confirming relevance via abstract from 
        another search tool, as full-text retrieval is data-intensive.
        """
        return ar5iv_search(query, top_k)
    
    @mcp.tool(name="Wikipedia Search", enabled=True)
    def wikipedia_search(topic: str) -> str:
        """
        Search Wikipedia for general knowledge and background information.
        
        Best for: Understanding scientific concepts, definitions, foundational 
        material properties, and general context before diving into research papers.
        
        Returns: Summary text of the topic with relevant background information.
        
        Args:
            topic: The topic or concept to look up (e.g., "neural networks", 
            "thermodynamics")
        """
        return _general_tools.wikipedia_tool.run(topic)