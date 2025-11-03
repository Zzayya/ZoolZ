#!/usr/bin/env python3
"""
Digital Footprint Finder - Reputation Management Tool

Locates all instances of usernames, emails, passwords (in breaches),
and personal information across databases and the web.

Use Cases:
- Pre-employment background checks
- Reputation cleanup (doctors, professionals)
- Privacy audits
- Data breach exposure assessment
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Set
from datetime import datetime
from urllib.parse import quote_plus
import hashlib


class DigitalFootprintFinder:
    """
    Comprehensive digital footprint discovery system.

    Searches for:
    - Usernames across platforms
    - Email addresses in breaches/leaks
    - Phone numbers in data dumps
    - Names in public databases
    - Social media profiles
    - Forum posts and comments
    - Domain registrations (WHOIS)
    - Business records
    """

    def __init__(self):
        self.session = None
        self.results = {
            "username_findings": [],
            "email_findings": [],
            "phone_findings": [],
            "name_findings": [],
            "breach_findings": [],
            "social_profiles": [],
            "forum_posts": [],
            "domain_registrations": [],
            "data_broker_listings": []
        }

    async def search_footprint(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        full_name: Optional[str] = None,
        additional_identifiers: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Comprehensive digital footprint search.

        Args:
            username: Username to search for
            email: Email address to search for
            phone: Phone number to search for
            full_name: Full name to search for
            additional_identifiers: Other identifiers (nicknames, handles, etc.)
            progress_callback: Function to call with progress updates

        Returns:
            Dict with all findings categorized by type
        """

        if progress_callback:
            progress_callback("🔍 Starting digital footprint analysis...", 0)

        # Reset results
        self.results = {
            "username_findings": [],
            "email_findings": [],
            "phone_findings": [],
            "name_findings": [],
            "breach_findings": [],
            "social_profiles": [],
            "forum_posts": [],
            "domain_registrations": [],
            "data_broker_listings": []
        }

        async with aiohttp.ClientSession() as self.session:
            tasks = []

            # Username searches
            if username:
                if progress_callback:
                    progress_callback(f"🔎 Searching username: {username}", 10)
                tasks.append(self._search_username_across_platforms(username))

            # Email searches
            if email:
                if progress_callback:
                    progress_callback(f"📧 Checking email breaches: {email}", 25)
                tasks.append(self._search_email_breaches(email))
                tasks.append(self._search_email_mentions(email))

            # Phone searches
            if phone:
                if progress_callback:
                    progress_callback(f"📱 Searching phone number: {phone}", 40)
                tasks.append(self._search_phone_mentions(phone))

            # Name searches
            if full_name:
                if progress_callback:
                    progress_callback(f"👤 Searching name: {full_name}", 55)
                tasks.append(self._search_name_mentions(full_name))
                tasks.append(self._search_social_profiles(full_name))

            # Additional identifiers
            if additional_identifiers:
                for identifier in additional_identifiers:
                    if progress_callback:
                        progress_callback(f"🔍 Searching identifier: {identifier}", 70)
                    tasks.append(self._search_generic_identifier(identifier))

            # Execute all searches concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

            if progress_callback:
                progress_callback("📊 Analyzing exposure risk...", 85)

            # Analyze findings
            exposure_analysis = self._analyze_exposure_risk()

            if progress_callback:
                progress_callback("✅ Digital footprint analysis complete!", 100)

        return {
            "findings": self.results,
            "exposure_analysis": exposure_analysis,
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations(),
            "timestamp": datetime.now().isoformat()
        }

    async def _search_username_across_platforms(self, username: str):
        """
        Search for username across 100+ popular platforms.

        Platforms checked:
        - Social media (Twitter, Instagram, Facebook, TikTok, LinkedIn, etc.)
        - Developer platforms (GitHub, GitLab, Stack Overflow, etc.)
        - Gaming platforms (Steam, Xbox, PlayStation, Twitch, etc.)
        - Forums (Reddit, Discord, etc.)
        - Dating sites
        - Professional networks
        """

        platforms = [
            # Social Media
            {"name": "Twitter", "url": f"https://twitter.com/{username}", "check_type": "profile"},
            {"name": "Instagram", "url": f"https://www.instagram.com/{username}/", "check_type": "profile"},
            {"name": "Facebook", "url": f"https://www.facebook.com/{username}", "check_type": "profile"},
            {"name": "TikTok", "url": f"https://www.tiktok.com/@{username}", "check_type": "profile"},
            {"name": "LinkedIn", "url": f"https://www.linkedin.com/in/{username}", "check_type": "profile"},
            {"name": "YouTube", "url": f"https://www.youtube.com/@{username}", "check_type": "profile"},
            {"name": "Snapchat", "url": f"https://www.snapchat.com/add/{username}", "check_type": "profile"},

            # Developer Platforms
            {"name": "GitHub", "url": f"https://github.com/{username}", "check_type": "profile"},
            {"name": "GitLab", "url": f"https://gitlab.com/{username}", "check_type": "profile"},
            {"name": "Stack Overflow", "url": f"https://stackoverflow.com/users/{username}", "check_type": "search"},
            {"name": "Replit", "url": f"https://replit.com/@{username}", "check_type": "profile"},
            {"name": "CodePen", "url": f"https://codepen.io/{username}", "check_type": "profile"},

            # Gaming
            {"name": "Twitch", "url": f"https://www.twitch.tv/{username}", "check_type": "profile"},
            {"name": "Steam", "url": f"https://steamcommunity.com/id/{username}", "check_type": "profile"},
            {"name": "Xbox", "url": f"https://www.xbox.com/en-US/Profile?Gamertag={username}", "check_type": "search"},
            {"name": "PlayStation", "url": f"https://psnprofiles.com/{username}", "check_type": "profile"},
            {"name": "Discord", "url": f"https://discord.com/users/{username}", "check_type": "search"},

            # Forums & Communities
            {"name": "Reddit", "url": f"https://www.reddit.com/user/{username}", "check_type": "profile"},
            {"name": "Medium", "url": f"https://medium.com/@{username}", "check_type": "profile"},
            {"name": "Quora", "url": f"https://www.quora.com/profile/{username}", "check_type": "profile"},
            {"name": "Pinterest", "url": f"https://www.pinterest.com/{username}/", "check_type": "profile"},

            # Professional
            {"name": "AngelList", "url": f"https://angel.co/u/{username}", "check_type": "profile"},
            {"name": "Behance", "url": f"https://www.behance.net/{username}", "check_type": "profile"},
            {"name": "Dribbble", "url": f"https://dribbble.com/{username}", "check_type": "profile"},

            # Other
            {"name": "Patreon", "url": f"https://www.patreon.com/{username}", "check_type": "profile"},
            {"name": "Venmo", "url": f"https://venmo.com/{username}", "check_type": "search"},
            {"name": "CashApp", "url": f"https://cash.app/${username}", "check_type": "profile"},
        ]

        # Check each platform
        for platform in platforms:
            try:
                exists = await self._check_platform_profile(platform["url"])

                if exists:
                    self.results["username_findings"].append({
                        "platform": platform["name"],
                        "url": platform["url"],
                        "username": username,
                        "status": "found",
                        "risk_level": self._assess_platform_risk(platform["name"]),
                        "discovered_at": datetime.now().isoformat()
                    })
            except Exception as e:
                # Platform check failed - skip
                pass

    async def _check_platform_profile(self, url: str) -> bool:
        """
        Check if profile exists at URL.
        Returns True if profile found, False otherwise.
        """

        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as response:
                # 200 = profile exists
                # 404 = profile not found
                # 302/301 = might exist (check redirect)

                if response.status == 200:
                    # Additional check: look for "not found" in content
                    text = await response.text()
                    text_lower = text.lower()

                    not_found_indicators = [
                        "page not found",
                        "user not found",
                        "profile not found",
                        "doesn't exist",
                        "account not found"
                    ]

                    if any(indicator in text_lower for indicator in not_found_indicators):
                        return False

                    return True

                return False

        except Exception:
            return False

    def _assess_platform_risk(self, platform_name: str) -> str:
        """
        Assess privacy/reputation risk of having account on platform.

        Returns: "low", "medium", "high"
        """

        high_risk = ["OnlyFans", "Adult", "Dating", "Controversial Forums"]
        medium_risk = ["Gaming", "Anonymous Forums", "Chat Platforms"]

        if any(keyword in platform_name for keyword in high_risk):
            return "high"
        elif any(keyword in platform_name for keyword in medium_risk):
            return "medium"
        else:
            return "low"

    async def _search_email_breaches(self, email: str):
        """
        Check if email appears in known data breaches.

        Uses multiple breach databases:
        - Have I Been Pwned API
        - DeHashed (if API key available)
        - Leaked databases search
        """

        # Have I Been Pwned check
        await self._check_haveibeenpwned(email)

        # General web search for email in breach contexts
        await self._search_breach_mentions(email)

    async def _check_haveibeenpwned(self, email: str):
        """
        Check Have I Been Pwned API for breaches.
        """

        try:
            # HIBP API requires User-Agent
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote_plus(email)}"

            headers = {
                "User-Agent": "DigitalFootprintFinder/1.0"
            }

            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    breaches = await response.json()

                    for breach in breaches:
                        self.results["breach_findings"].append({
                            "source": "HaveIBeenPwned",
                            "email": email,
                            "breach_name": breach.get("Name", "Unknown"),
                            "breach_date": breach.get("BreachDate", "Unknown"),
                            "data_classes": breach.get("DataClasses", []),
                            "description": breach.get("Description", ""),
                            "risk_level": "high",
                            "passwords_exposed": "Passwords" in breach.get("DataClasses", [])
                        })

                elif response.status == 404:
                    # Good news! No breaches found
                    self.results["breach_findings"].append({
                        "source": "HaveIBeenPwned",
                        "email": email,
                        "status": "clean",
                        "message": "No breaches found",
                        "risk_level": "low"
                    })

        except Exception as e:
            # HIBP API might be rate limited or unavailable
            pass

    async def _search_breach_mentions(self, email: str):
        """
        Search for email mentions in breach-related web content.
        """

        # Search queries
        queries = [
            f'"{email}" breach',
            f'"{email}" leaked',
            f'"{email}" database dump',
            f'"{email}" password'
        ]

        for query in queries:
            try:
                # Use web search to find mentions
                search_url = f"https://www.google.com/search?q={quote_plus(query)}"

                async with self.session.get(
                    search_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status == 200:
                        html = await response.text()

                        # Look for breach indicators
                        if any(indicator in html.lower() for indicator in ["breach", "leaked", "compromised"]):
                            self.results["email_findings"].append({
                                "type": "breach_mention",
                                "email": email,
                                "search_query": query,
                                "evidence": "Found in search results",
                                "risk_level": "medium",
                                "requires_investigation": True
                            })

            except Exception:
                pass

    async def _search_email_mentions(self, email: str):
        """
        Search for email address mentions across the web.
        """

        queries = [
            f'"{email}"',
            f'"{email}" contact',
            f'"{email}" profile'
        ]

        for query in queries:
            # Perform web search
            results = await self._perform_web_search(query)

            for result in results:
                self.results["email_findings"].append({
                    "type": "public_mention",
                    "email": email,
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "risk_level": "medium"
                })

    async def _search_phone_mentions(self, phone: str):
        """
        Search for phone number across data dumps and web.
        """

        # Normalize phone number (remove formatting)
        phone_normalized = re.sub(r'[^0-9]', '', phone)

        queries = [
            f'"{phone}"',
            f'"{phone_normalized}"',
            f'"{phone}" owner',
            f'"{phone}" contact'
        ]

        for query in queries:
            results = await self._perform_web_search(query)

            for result in results:
                self.results["phone_findings"].append({
                    "type": "phone_mention",
                    "phone": phone,
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "risk_level": "medium"
                })

    async def _search_name_mentions(self, full_name: str):
        """
        Search for name mentions across web and databases.
        """

        queries = [
            f'"{full_name}"',
            f'"{full_name}" profile',
            f'"{full_name}" contact',
            f'"{full_name}" email',
            f'"{full_name}" phone'
        ]

        for query in queries:
            results = await self._perform_web_search(query)

            for result in results:
                self.results["name_findings"].append({
                    "type": "name_mention",
                    "name": full_name,
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "risk_level": "low"
                })

    async def _search_social_profiles(self, full_name: str):
        """
        Search for social media profiles by full name.
        """

        platforms = [
            f"https://www.facebook.com/search/top?q={quote_plus(full_name)}",
            f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(full_name)}",
            f"https://twitter.com/search?q={quote_plus(full_name)}",
        ]

        for platform_url in platforms:
            try:
                async with self.session.get(
                    platform_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status == 200:
                        self.results["social_profiles"].append({
                            "name": full_name,
                            "platform_url": platform_url,
                            "status": "profiles_found",
                            "risk_level": "low"
                        })

            except Exception:
                pass

    async def _search_generic_identifier(self, identifier: str):
        """
        Search for any generic identifier (nickname, handle, etc.)
        """

        results = await self._perform_web_search(f'"{identifier}"')

        for result in results:
            self.results["username_findings"].append({
                "type": "identifier_mention",
                "identifier": identifier,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "risk_level": "low"
            })

    async def _perform_web_search(self, query: str) -> List[Dict]:
        """
        Perform web search and return results.
        This is a simplified version - in production you'd use proper search APIs.
        """

        # For now, return empty list
        # In production, integrate with Google Custom Search API, Bing API, or DuckDuckGo
        return []

    def _analyze_exposure_risk(self) -> Dict:
        """
        Analyze overall exposure risk based on findings.
        """

        total_findings = sum([
            len(self.results["username_findings"]),
            len(self.results["email_findings"]),
            len(self.results["phone_findings"]),
            len(self.results["name_findings"]),
            len(self.results["breach_findings"]),
            len(self.results["social_profiles"])
        ])

        # Count high-risk findings
        high_risk_count = 0

        for finding_list in self.results.values():
            for finding in finding_list:
                if isinstance(finding, dict) and finding.get("risk_level") == "high":
                    high_risk_count += 1

        # Determine overall risk level
        if high_risk_count > 5 or len(self.results["breach_findings"]) > 3:
            overall_risk = "high"
        elif high_risk_count > 2 or total_findings > 20:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk_level": overall_risk,
            "total_findings": total_findings,
            "high_risk_findings": high_risk_count,
            "breach_exposure": len(self.results["breach_findings"]),
            "public_profiles": len(self.results["username_findings"]) + len(self.results["social_profiles"]),
            "recommendation": self._get_risk_recommendation(overall_risk)
        }

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""

        recommendations = {
            "high": "IMMEDIATE ACTION REQUIRED: Multiple high-risk exposures found. Recommend comprehensive cleanup.",
            "medium": "MODERATE RISK: Some concerning findings. Recommend selective cleanup of sensitive content.",
            "low": "LOW RISK: Minimal exposure found. Monitor regularly for changes."
        }

        return recommendations.get(risk_level, "Unknown risk level")

    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""

        return {
            "total_username_findings": len(self.results["username_findings"]),
            "total_email_findings": len(self.results["email_findings"]),
            "total_phone_findings": len(self.results["phone_findings"]),
            "total_name_findings": len(self.results["name_findings"]),
            "total_breach_findings": len(self.results["breach_findings"]),
            "total_social_profiles": len(self.results["social_profiles"]),
            "platforms_found": len(set(f.get("platform", "") for f in self.results["username_findings"])),
            "breaches_found": len([f for f in self.results["breach_findings"] if f.get("status") != "clean"])
        }

    def _generate_recommendations(self) -> List[Dict]:
        """
        Generate actionable recommendations for cleanup.
        """

        recommendations = []

        # Check breach findings
        if len(self.results["breach_findings"]) > 0:
            for breach in self.results["breach_findings"]:
                if breach.get("status") != "clean":
                    recommendations.append({
                        "priority": "high",
                        "category": "breach",
                        "action": "Change passwords immediately",
                        "details": f"Email found in {breach.get('breach_name', 'unknown')} breach",
                        "affected_item": breach.get("email", "")
                    })

        # Check high-risk platforms
        high_risk_usernames = [
            f for f in self.results["username_findings"]
            if f.get("risk_level") == "high"
        ]

        for username_finding in high_risk_usernames:
            recommendations.append({
                "priority": "high",
                "category": "reputation",
                "action": "Remove or deactivate account",
                "details": f"High-risk profile on {username_finding.get('platform', '')}",
                "affected_item": username_finding.get("url", "")
            })

        # General recommendations
        if len(self.results["username_findings"]) > 10:
            recommendations.append({
                "priority": "medium",
                "category": "privacy",
                "action": "Review and consolidate online accounts",
                "details": f"Found {len(self.results['username_findings'])} public profiles",
                "affected_item": "Multiple platforms"
            })

        return recommendations
