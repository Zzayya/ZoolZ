#!/usr/bin/env python3
"""
Web Scraper for Social Media and Web Mentions
Performs respectful, rate-limited searches across the web
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import quote_plus


class WebSearcher:
    """
    Performs web searches to find social media profiles, web mentions, etc.
    Uses Google Custom Search API (100 free queries/day) and respectful scraping.
    """
    
    # Google Custom Search API (get free key at: https://developers.google.com/custom-search)
    GOOGLE_API_KEY = None
    GOOGLE_SEARCH_ENGINE_ID = None
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None
    ):
        """
        Initialize web searcher.
        
        Args:
            google_api_key: Google API key (free tier: 100 queries/day)
            search_engine_id: Custom Search Engine ID
        """
        self.google_api_key = google_api_key
        self.search_engine_id = search_engine_id
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        self.daily_query_count = 0
        self.max_daily_queries = 100  # Free tier limit
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/91.0.4472.124 Safari/537.36"
                }
            )
        return self.session
    
    async def search(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict:
        """
        Perform a web search using Google Custom Search API or fallback methods.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)
            
        Returns:
            Dict containing search results
        """
        
        # Check rate limits
        if self.daily_query_count >= self.max_daily_queries:
            return {
                "query": query,
                "results": [],
                "error": "Daily query limit reached (100 queries/day on free tier)"
            }
        
        self.daily_query_count += 1
        
        # Try Google Custom Search API first
        if self.google_api_key and self.search_engine_id:
            return await self._google_custom_search(query, num_results)
        
        # Fallback to DuckDuckGo (no API key needed, but more limited)
        return await self._duckduckgo_search(query, num_results)
    
    async def _google_custom_search(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict:
        """
        Use Google Custom Search API.
        Free tier: 100 queries/day
        Sign up: https://developers.google.com/custom-search/v1/overview
        """
        
        try:
            session = await self._get_session()
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10)  # Max 10 per request
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for item in data.get("items", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "Google Custom Search"
                        })
                    
                    return {
                        "query": query,
                        "results": results,
                        "total_results": data.get("searchInformation", {}).get("totalResults", 0)
                    }
                else:
                    error_data = await response.json()
                    return {
                        "query": query,
                        "results": [],
                        "error": error_data.get("error", {}).get("message", "Unknown error")
                    }
        
        except Exception as e:
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    async def _duckduckgo_search(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict:
        """
        Fallback search using DuckDuckGo HTML (no API key needed).
        This is more limited and may be blocked if overused.
        """
        
        try:
            session = await self._get_session()
            
            # DuckDuckGo HTML search
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    result_divs = soup.find_all('div', class_='result')[:num_results]
                    
                    for div in result_divs:
                        title_elem = div.find('a', class_='result__a')
                        snippet_elem = div.find('a', class_='result__snippet')
                        
                        if title_elem:
                            results.append({
                                "title": title_elem.get_text(strip=True),
                                "url": title_elem.get('href', ''),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                "source": "DuckDuckGo"
                            })
                    
                    return {
                        "query": query,
                        "results": results
                    }
        
        except Exception as e:
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
        
        return {"query": query, "results": []}
    
    async def search_social_media(
        self,
        name: str,
        additional_info: Optional[str] = None
    ) -> Dict:
        """
        Search specifically for social media profiles.
        
        Args:
            name: Person's name
            additional_info: City, state, or other identifying info
            
        Returns:
            Dict of social media profiles organized by platform
        """
        
        social_results = {
            "facebook": [],
            "linkedin": [],
            "twitter": [],
            "instagram": [],
            "tiktok": []
        }
        
        # Build targeted queries for each platform
        platforms = {
            "facebook": f'site:facebook.com "{name}"',
            "linkedin": f'site:linkedin.com/in "{name}"',
            "twitter": f'site:twitter.com "{name}"',
            "instagram": f'site:instagram.com "{name}"',
            "tiktok": f'site:tiktok.com "@{name.replace(" ", "")}"'
        }
        
        # Add additional info to queries if provided
        if additional_info:
            for platform in platforms:
                platforms[platform] += f' "{additional_info}"'
        
        # Search each platform
        for platform_name, query in platforms.items():
            try:
                search_result = await self.search(query, num_results=5)
                social_results[platform_name] = search_result.get("results", [])
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                social_results[platform_name] = {"error": str(e)}
        
        return social_results
    
    async def search_phone_mentions(self, phone: str) -> List[Dict]:
        """
        Enhanced phone search with multiple formats and reverse lookup sites.
        Searches for phone number mentions including:
        - Business listings
        - Contact pages
        - Public directories
        - Reverse phone lookup results
        - Forum posts and reviews
        """

        # Normalize phone to digits only
        digits_only = re.sub(r'\D', '', phone)

        # Generate comprehensive format variations for better search coverage
        formats = []

        if len(digits_only) >= 10:
            # Extract last 10 digits (US phone number)
            last_10 = digits_only[-10:]
            area_code = last_10[0:3]
            prefix = last_10[3:6]
            line = last_10[6:10]

            formats = [
                phone,  # Original format (as provided by user)
                last_10,  # Digits only: 7408276423
                f"{area_code}-{prefix}-{line}",  # Dashed: 740-827-6423
                f"({area_code}) {prefix}-{line}",  # Standard: (740) 827-6423
                f"{area_code}.{prefix}.{line}",  # Dotted: 740.827.6423
                f"{area_code} {prefix} {line}",  # Spaced: 740 827 6423
                f"+1-{area_code}-{prefix}-{line}",  # International: +1-740-827-6423
                f"1-{area_code}-{prefix}-{line}",  # With country code: 1-740-827-6423
                f"({area_code}){prefix}{line}",  # No spacing: (740)8276423
            ]
        else:
            # Fallback for non-standard formats
            formats = [phone, digits_only]

        all_results = []
        seen_urls = set()

        # Search multiple query types for comprehensive coverage
        query_templates = [
            '"{format}" contact OR "phone number" OR "call"',
            '"{format}" site:whitepages.com OR site:truecaller.com OR site:spokeo.com',
            '"{format}" "owner" OR "belongs to" OR "registered to"',
            '"{format}" business OR company OR professional',
            '"{format}" reviews OR complaints OR scam OR spam'
        ]

        # Use the 3 most common formats to avoid excessive queries
        primary_formats = formats[0:3] if len(formats) >= 3 else formats

        for phone_format in primary_formats:
            for template in query_templates:
                try:
                    query = template.format(format=phone_format)
                    search_result = await self.search(query, num_results=5)

                    # Add results and extract associated names
                    for result in search_result.get("results", []):
                        url = result.get("url", "")

                        # Skip duplicates
                        if url and url not in seen_urls:
                            seen_urls.add(url)

                            # Try to extract associated names from snippet
                            snippet = result.get("snippet", "")
                            title = result.get("title", "")
                            result["associated_names"] = self._extract_names_from_text(
                                snippet + " " + title
                            )

                            all_results.append(result)

                    # Rate limiting - be polite
                    await asyncio.sleep(self.rate_limit_delay)

                except Exception as e:
                    # Continue on error, don't let one failed query stop the rest
                    continue

        return all_results

    def _extract_names_from_text(self, text: str) -> List[str]:
        """
        Extract potential person names from text.
        Looks for capitalized words that might be names.
        """

        # Pattern: 2-4 capitalized words in sequence (likely a name)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        potential_names = re.findall(name_pattern, text)

        # Filter out common non-name words
        excluded_words = {
            'About', 'Contact', 'Phone', 'Email', 'Address', 'Home', 'Business',
            'Search', 'Find', 'Lookup', 'Directory', 'Results', 'Reviews',
            'United States', 'North America', 'Customer Service'
        }

        filtered_names = []
        for name in potential_names:
            # Skip if contains excluded words
            if not any(excluded in name for excluded in excluded_words):
                # Skip if too short (single word) or too long (likely not a name)
                word_count = len(name.split())
                if 2 <= word_count <= 4:
                    filtered_names.append(name)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(filtered_names))
    
    async def search_email_mentions(self, email: str) -> List[Dict]:
        """
        Search for mentions of an email address on the web.
        """
        
        try:
            query = f'"{email}" contact OR profile OR about'
            search_result = await self.search(query, num_results=15)
            return search_result.get("results", [])
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch the full HTML content of a webpage.
        Used for deeper analysis of search results.
        """
        
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        
        except Exception:
            return None
        
        return None
    
    def extract_emails_from_text(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def extract_phones_from_text(self, text: str) -> List[str]:
        """
        Extract phone numbers from text with enhanced pattern matching.
        Handles multiple formats including international numbers.
        """

        phone_patterns = [
            # Standard formats
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 123-456-7890 or 123.456.7890
            r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123)456-7890
            r'\d{10}',  # 1234567890 (10 digits)

            # With country code
            r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
            r'1[-.\s]\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # 1-123-456-7890

            # International format
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # +XX XXX XXX XXXX

            # Extensions
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}[\s]?(?:ext|x|extension)[\s]?\d{2,5}',  # With extension
        ]

        found = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)

        # Normalize and validate results
        validated = []
        for phone in found:
            # Remove common false positives (like dates, IDs, etc.)
            digits = re.sub(r'\D', '', phone)

            # Valid US phone numbers should have 10 or 11 digits
            if len(digits) == 10 or (len(digits) == 11 and digits[0] == '1'):
                validated.append(phone)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated))
    
    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()


# Helper function to identify social media platforms from URLs
def identify_social_platform(url: str) -> Optional[str]:
    """
    Identify which social media platform a URL belongs to.
    Returns platform name or None.
    """
    
    platforms = {
        "facebook.com": "Facebook",
        "linkedin.com": "LinkedIn",
        "twitter.com": "Twitter",
        "x.com": "Twitter",
        "instagram.com": "Instagram",
        "tiktok.com": "TikTok",
        "youtube.com": "YouTube",
        "snapchat.com": "Snapchat",
        "pinterest.com": "Pinterest"
    }
    
    for domain, platform_name in platforms.items():
        if domain in url:
            return platform_name
    
    return None
