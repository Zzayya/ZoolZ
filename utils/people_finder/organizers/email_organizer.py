#!/usr/bin/env python3
"""
Email Organizer
Professional-grade email organization
ONE JOB: Process, deduplicate, and organize email addresses
"""

from typing import Dict, List, Tuple


class EmailOrganizer:
    """
    Organizes emails with:
    - Deduplication
    - Domain validation and reputation
    - Business vs personal detection
    - Format pattern analysis
    - Email provider detection
    - Confidence scoring per email
    """

    # Known email providers
    PERSONAL_PROVIDERS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
        'zoho.com', 'yandex.com', 'gmx.com', 'mail.ru'
    }

    # Disposable/temporary email domains
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', 'temp-mail.org', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'tempmail.com',
        'sharklasers.com', 'guerrillamailblock.com'
    }

    # Provider mapping
    PROVIDER_MAP = {
        'gmail.com': 'Gmail',
        'googlemail.com': 'Gmail',
        'yahoo.com': 'Yahoo',
        'ymail.com': 'Yahoo',
        'hotmail.com': 'Hotmail',
        'outlook.com': 'Outlook',
        'live.com': 'Outlook',
        'msn.com': 'MSN',
        'aol.com': 'AOL',
        'icloud.com': 'iCloud',
        'me.com': 'iCloud',
        'mac.com': 'iCloud',
        'protonmail.com': 'ProtonMail',
        'pm.me': 'ProtonMail',
        'zoho.com': 'Zoho',
        'yandex.com': 'Yandex',
        'mail.ru': 'Mail.ru',
        'gmx.com': 'GMX',
        'fastmail.com': 'FastMail'
    }

    def __init__(self, confidence_scorer=None):
        """
        Initialize email organizer.

        Args:
            confidence_scorer: ConfidenceScorer instance (optional)
        """
        self.confidence_scorer = confidence_scorer

    def organize_emails(self, person: Dict) -> List[Dict]:
        """
        Organize all emails for a person.

        Args:
            person: Person dict with emails and sources

        Returns:
            List of organized email dicts with full metadata
        """
        raw_emails = person.get("emails", [])

        if not raw_emails:
            return []

        # Deduplicate emails
        unique_emails = list(dict.fromkeys([e.lower() for e in raw_emails if e]))

        organized = []

        for email in unique_emails:
            # Parse email components
            local_part, domain = self._parse_email(email)

            # Detect email type and provider
            email_type = self._detect_email_type(email, domain)
            provider = self._detect_email_provider(domain)

            # Analyze format pattern
            format_type = self._analyze_email_format(local_part, person.get("name", ""))

            # Calculate confidence
            if self.confidence_scorer:
                confidence = self.confidence_scorer.calculate_email_confidence(
                    email,
                    person.get("confidence_sources", []),
                    domain
                )
            else:
                confidence = "medium"

            # Validate domain
            is_valid_domain = self._is_valid_email_domain(domain)

            # Count sources
            source_count = self._count_email_mentions(email, person)

            email_data = {
                "email": email,
                "local_part": local_part,
                "domain": domain,
                "email_type": email_type,  # personal, business, disposable
                "provider": provider,  # Gmail, Yahoo, Outlook, Corporate, etc.
                "format_type": format_type,  # first.last, flast, etc.
                "is_business_email": email_type == "business",
                "is_disposable": email_type == "disposable",
                "is_valid_domain": is_valid_domain,
                "confidence": confidence,
                "confidence_percent": self._confidence_to_percent(confidence),
                "source_count": source_count,
                "sources": self._get_email_sources(email, person)
            }

            organized.append(email_data)

        # Sort by confidence (highest first)
        organized.sort(key=lambda x: x["confidence_percent"], reverse=True)

        return organized

    def _parse_email(self, email: str) -> Tuple[str, str]:
        """Parse email into local part and domain"""
        if '@' in email:
            parts = email.split('@')
            return parts[0], parts[1] if len(parts) == 2 else ""
        return email, ""

    def _detect_email_type(self, email: str, domain: str) -> str:
        """Detect if email is personal, business, or disposable"""
        if domain in self.DISPOSABLE_DOMAINS:
            return "disposable"

        if domain in self.PERSONAL_PROVIDERS:
            return "personal"

        # If not personal or disposable, assume business
        return "business"

    def _detect_email_provider(self, domain: str) -> str:
        """Detect email provider"""
        provider = self.PROVIDER_MAP.get(domain)
        if provider:
            return provider

        # Check if it's a corporate domain
        if '.' in domain and domain not in ['gmail.com', 'yahoo.com']:
            return f"Corporate ({domain})"

        return "Unknown"

    def _analyze_email_format(self, local_part: str, person_name: str) -> str:
        """Analyze email format pattern"""
        if not person_name:
            return "unknown"

        # Normalize name
        name_parts = person_name.lower().split()
        if len(name_parts) < 2:
            return "unknown"

        first_name = name_parts[0]
        last_name = name_parts[-1]
        local_lower = local_part.lower()

        # Common patterns
        if local_lower == f"{first_name}.{last_name}":
            return "first.last"
        elif local_lower == f"{first_name}{last_name}":
            return "firstlast"
        elif local_lower == f"{first_name[0]}{last_name}":
            return "flast"
        elif local_lower == f"{first_name}{last_name[0]}":
            return "firstl"
        elif local_lower == f"{first_name}_{last_name}":
            return "first_last"
        elif local_lower == f"{last_name}.{first_name}":
            return "last.first"
        elif local_lower == f"{last_name}{first_name}":
            return "lastfirst"
        elif first_name in local_lower or last_name in local_lower:
            return "contains_name"

        return "custom"

    def _is_valid_email_domain(self, domain: str) -> bool:
        """Basic domain validation"""
        if not domain:
            return False

        # Must have at least one dot
        if '.' not in domain:
            return False

        # Must not start or end with dot or dash
        if domain.startswith('.') or domain.startswith('-'):
            return False
        if domain.endswith('.') or domain.endswith('-'):
            return False

        # Must have valid TLD (at least 2 chars after last dot)
        parts = domain.split('.')
        if len(parts) < 2 or len(parts[-1]) < 2:
            return False

        return True

    def _count_email_mentions(self, email: str, person: Dict) -> int:
        """Count how many times this email appears"""
        count = 0

        # Check public records
        for record in person.get("public_records", []):
            if isinstance(record, dict):
                if email.lower() in str(record).lower():
                    count += 1

        # Check web mentions
        for mention in person.get("web_mentions", []):
            if isinstance(mention, dict):
                if email.lower() in str(mention).lower():
                    count += 1

        return max(count, 1)

    def _get_email_sources(self, email: str, person: Dict) -> List[str]:
        """Get list of sources where this email was found"""
        sources = []

        if "public_records" in person.get("confidence_sources", []):
            sources.append("Public Records")

        if "user_input" in person.get("confidence_sources", []):
            sources.append("User Input")

        if "web_mention" in person.get("confidence_sources", []):
            sources.append("Web Search")

        if "social_media" in person.get("confidence_sources", []):
            sources.append("Social Media")

        return sources if sources else ["Unknown"]

    def _confidence_to_percent(self, confidence: str) -> int:
        """Convert confidence level to percentage"""
        mapping = {"high": 85, "medium": 60, "low": 35}
        return mapping.get(confidence, 50)
