"""
Web Search Client for finding official sources
"""
import logging
from typing import List, Dict, Any
import httpx
from serpapi import GoogleSearch
from duckduckgo_search import DDGS

from config import settings

logger = logging.getLogger(__name__)


class WebSearchClient:
    """Client for web search operations"""

    def __init__(self):
        self.provider = settings.WEB_SEARCH_PROVIDER
        self.max_results = settings.MAX_SEARCH_RESULTS

        logger.info(f"Web search client initialized: {self.provider}")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search

        Args:
            query: Search query string

        Returns:
            List of search results with title, url, snippet
        """
        try:
            if self.provider == "serpapi":
                results = await self._search_serpapi(query)
            elif self.provider == "brave":
                results = await self._search_brave(query)
            elif self.provider == "duckduckgo":
                results = await self._search_duckduckgo(query)
            else:
                raise ValueError(f"Unsupported search provider: {self.provider}")

            logger.info(f"Search '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return []

    async def _search_serpapi(self, query: str) -> List[Dict[str, Any]]:
        """Search using SerpAPI (Google)"""
        if not settings.SERP_API_KEY:
            raise ValueError("SERP_API_KEY not set")

        search = GoogleSearch({
            "q": query,
            "api_key": settings.SERP_API_KEY,
            "num": self.max_results
        })

        results = search.get_dict()

        # Extract organic results
        organic = results.get("organic_results", [])

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", "")
            }
            for r in organic
        ]

    async def _search_brave(self, query: str) -> List[Dict[str, Any]]:
        """Search using Brave Search API"""
        if not settings.BRAVE_SEARCH_API_KEY:
            raise ValueError("BRAVE_SEARCH_API_KEY not set")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY
        }
        params = {
            "q": query,
            "count": self.max_results
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            web_results = data.get("web", {}).get("results", [])

            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("description", "")
                }
                for r in web_results
            ]

    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (free, no API key required)

        Uses duckduckgo-search library which provides instant results
        without requiring any authentication or API keys.

        Note: DuckDuckGo has aggressive rate limiting. We add delays to avoid blocks.
        """
        try:
            # DuckDuckGo search is synchronous, but we wrap it for async compatibility
            import asyncio
            import time

            def _sync_search():
                # Add 2-3 second delay before each search to avoid rate limiting
                time.sleep(2.5)

                with DDGS() as ddgs:
                    # Get text search results
                    results = list(ddgs.text(
                        query,
                        max_results=self.max_results,
                        region='us-en',  # Focus on US results
                        safesearch='off'
                    ))
                    return results

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _sync_search)

            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            # If rate limited, wait longer before returning empty results
            if "Ratelimit" in str(e):
                logger.warning("Rate limited by DuckDuckGo, waiting 10 seconds...")
                await asyncio.sleep(10)
            return []

    async def fetch_page_content(self, url: str) -> str:
        """
        Fetch and extract text content from a URL

        Returns cleaned text content
        """
        try:
            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
                follow_redirects=settings.FOLLOW_REDIRECTS
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": settings.USER_AGENT}
                )
                response.raise_for_status()

                # Extract text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)

                return text

        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return ""
