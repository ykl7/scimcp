# General_tools.py

import os, requests
from langchain.tools import Tool
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.agent_toolkits.load_tools import load_tools

class General_ToolManager:
    def __init__(self):
        self.wikipedia_tool = self._load_wikipedia_tool()
        self.arxiv_tool = self._load_arxiv_tool()

    def _load_wikipedia_tool(self):
        wrapper = WikipediaAPIWrapper()
        wiki = WikipediaQueryRun(api_wrapper=wrapper)
        return Tool(
            name="Wikipedia Search",
            func=wiki.run,
            description="Get summaries of scientific concepts or background knowledge from Wikipedia."
        )

    def _load_arxiv_tool(self):
        arxiv = load_tools(["arxiv"])[0]
        return Tool(
            name="Arxiv Search",
            func=arxiv.run,
            description="Search academic papers on arXiv."
        )

    def google_scholar_search(self, topic: str, num_results: int = 5) -> list[dict]:
        params = {
            "engine": "google_scholar",
            "q": topic,
            "num": num_results,
            "api_key": os.environ["SERP_API_KEY"]
        }
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        return self._extract_google_scholar_papers(response.json())

    def semantic_scholar_search(self, query: str, result_limit: int = 5) -> list[dict]:
        fields = "title,abstract,citationCount,tldr,fieldsOfStudy,year,authors,isOpenAccess,openAccessPdf,url,venue"
        response = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            headers={'X-API-KEY': os.environ["SEMANTIC_SCHOLAR_API"]},
            params={'query': query, 'limit': result_limit, 'fields': fields}
        )
        response.raise_for_status()
        return self._extract_semantic_scholar_papers(response.json().get("data", []))

    def _extract_google_scholar_papers(self, data: dict): #Just clearer functions, no need for the user to acess this
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

    def _extract_semantic_scholar_papers(self, results: list[dict]):
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
                "abstract": abstract.strip(),
                "venue": venue,
                "cited_by": cited,
                "link": link,
                "pdf_url": pdf_url
            })
        return papers
