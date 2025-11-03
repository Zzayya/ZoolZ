#!/usr/bin/env python3
"""
Exposure Analyzer - Reputation Risk Assessment

Analyzes digital footprint findings to:
- Prioritize cleanup actions
- Generate removal/takedown requests
- Score reputation risk
- Track cleanup progress
"""

from typing import Dict, List
from datetime import datetime
import json


class ExposureAnalyzer:
    """
    Analyzes digital footprint exposure and generates cleanup strategies.
    """

    def __init__(self):
        self.risk_weights = {
            "breach": 10,  # Highest priority
            "high_risk_platform": 8,
            "personal_info_exposed": 7,
            "public_email": 5,
            "public_phone": 6,
            "social_profile": 3,
            "username_finding": 2,
            "name_mention": 1
        }

    def analyze_findings(self, findings: Dict) -> Dict:
        """
        Comprehensive analysis of all findings.

        Returns:
            - Risk score (0-100)
            - Prioritized action list
            - Category breakdown
            - Cleanup estimates
        """

        risk_score = self._calculate_risk_score(findings)
        prioritized_actions = self._prioritize_actions(findings)
        category_breakdown = self._break_down_by_category(findings)
        cleanup_estimate = self._estimate_cleanup_effort(findings)
        vulnerability_assessment = self._assess_vulnerabilities(findings)

        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "prioritized_actions": prioritized_actions,
            "category_breakdown": category_breakdown,
            "cleanup_estimate": cleanup_estimate,
            "vulnerability_assessment": vulnerability_assessment,
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_risk_score(self, findings: Dict) -> int:
        """
        Calculate overall risk score (0-100).

        Higher score = more exposure/risk
        """

        score = 0

        # Breaches are critical
        breach_findings = findings.get("breach_findings", [])
        for breach in breach_findings:
            if breach.get("status") != "clean":
                score += 10
                if breach.get("passwords_exposed"):
                    score += 5  # Extra points for password exposure

        # High-risk platforms
        username_findings = findings.get("username_findings", [])
        for finding in username_findings:
            if finding.get("risk_level") == "high":
                score += 8
            elif finding.get("risk_level") == "medium":
                score += 4
            else:
                score += 2

        # Email exposure
        email_findings = findings.get("email_findings", [])
        score += len(email_findings) * 3

        # Phone exposure
        phone_findings = findings.get("phone_findings", [])
        score += len(phone_findings) * 4

        # Name mentions (less critical but still matters)
        name_findings = findings.get("name_findings", [])
        score += len(name_findings) * 1

        # Cap at 100
        return min(score, 100)

    def _get_risk_level(self, risk_score: int) -> str:
        """Convert numeric score to risk level"""

        if risk_score >= 70:
            return "CRITICAL"
        elif risk_score >= 50:
            return "HIGH"
        elif risk_score >= 30:
            return "MEDIUM"
        elif risk_score >= 10:
            return "LOW"
        else:
            return "MINIMAL"

    def _prioritize_actions(self, findings: Dict) -> List[Dict]:
        """
        Generate prioritized list of cleanup actions.

        Returns actions sorted by urgency.
        """

        actions = []

        # PRIORITY 1: Data breaches
        for breach in findings.get("breach_findings", []):
            if breach.get("status") != "clean":
                actions.append({
                    "priority": 1,
                    "urgency": "IMMEDIATE",
                    "category": "Breach Exposure",
                    "action": "Change all passwords",
                    "details": f"Email compromised in {breach.get('breach_name', 'breach')}",
                    "affected_item": breach.get("email", ""),
                    "breach_date": breach.get("breach_date", "Unknown"),
                    "data_exposed": breach.get("data_classes", []),
                    "estimated_time": "30 minutes",
                    "difficulty": "Easy"
                })

        # PRIORITY 2: High-risk platforms
        for finding in findings.get("username_findings", []):
            if finding.get("risk_level") == "high":
                actions.append({
                    "priority": 2,
                    "urgency": "HIGH",
                    "category": "Reputation Risk",
                    "action": "Remove/deactivate account",
                    "details": f"High-risk profile on {finding.get('platform', 'unknown platform')}",
                    "affected_item": finding.get("url", ""),
                    "platform": finding.get("platform", ""),
                    "estimated_time": "15 minutes",
                    "difficulty": "Easy"
                })

        # PRIORITY 3: Public contact info
        for finding in findings.get("email_findings", []):
            if finding.get("type") == "public_mention":
                actions.append({
                    "priority": 3,
                    "urgency": "MEDIUM",
                    "category": "Privacy",
                    "action": "Request removal from website",
                    "details": f"Email publicly listed on {finding.get('url', 'website')}",
                    "affected_item": finding.get("email", ""),
                    "url": finding.get("url", ""),
                    "estimated_time": "1 hour",
                    "difficulty": "Medium",
                    "removal_method": "Contact webmaster or use GDPR request"
                })

        for finding in findings.get("phone_findings", []):
            actions.append({
                "priority": 3,
                "urgency": "MEDIUM",
                "category": "Privacy",
                "action": "Request removal from listing",
                "details": f"Phone number publicly listed",
                "affected_item": finding.get("phone", ""),
                "url": finding.get("url", ""),
                "estimated_time": "1 hour",
                "difficulty": "Medium",
                "removal_method": "Contact site admin or use opt-out form"
            })

        # PRIORITY 4: Medium-risk platforms
        for finding in findings.get("username_findings", []):
            if finding.get("risk_level") == "medium":
                actions.append({
                    "priority": 4,
                    "urgency": "MEDIUM",
                    "category": "Digital Footprint",
                    "action": "Review and consider removing",
                    "details": f"Profile on {finding.get('platform', 'platform')}",
                    "affected_item": finding.get("url", ""),
                    "estimated_time": "10 minutes",
                    "difficulty": "Easy"
                })

        # PRIORITY 5: Social media cleanup
        social_profiles = findings.get("social_profiles", [])
        if len(social_profiles) > 5:
            actions.append({
                "priority": 5,
                "urgency": "LOW",
                "category": "Social Media",
                "action": "Audit social media privacy settings",
                "details": f"Found {len(social_profiles)} social profiles - review privacy settings",
                "affected_item": "Multiple platforms",
                "estimated_time": "2 hours",
                "difficulty": "Medium"
            })

        # Sort by priority
        actions.sort(key=lambda x: x["priority"])

        return actions

    def _break_down_by_category(self, findings: Dict) -> Dict:
        """
        Break down findings by category for visualization.
        """

        return {
            "breach_exposure": {
                "count": len([f for f in findings.get("breach_findings", []) if f.get("status") != "clean"]),
                "severity": "critical",
                "description": "Email addresses found in data breaches"
            },
            "username_exposure": {
                "count": len(findings.get("username_findings", [])),
                "severity": "medium",
                "description": "Usernames found across platforms",
                "platforms": list(set(f.get("platform", "") for f in findings.get("username_findings", [])))
            },
            "email_exposure": {
                "count": len(findings.get("email_findings", [])),
                "severity": "high",
                "description": "Email addresses publicly listed"
            },
            "phone_exposure": {
                "count": len(findings.get("phone_findings", [])),
                "severity": "high",
                "description": "Phone numbers publicly listed"
            },
            "social_media_presence": {
                "count": len(findings.get("social_profiles", [])),
                "severity": "low",
                "description": "Social media profiles found"
            },
            "name_mentions": {
                "count": len(findings.get("name_findings", [])),
                "severity": "low",
                "description": "Public mentions of name"
            }
        }

    def _estimate_cleanup_effort(self, findings: Dict) -> Dict:
        """
        Estimate time and difficulty for complete cleanup.
        """

        total_actions = sum([
            len(findings.get("breach_findings", [])),
            len(findings.get("username_findings", [])),
            len(findings.get("email_findings", [])),
            len(findings.get("phone_findings", []))
        ])

        # Estimate hours
        estimated_hours = 0

        # Breaches: 30 min each
        estimated_hours += len(findings.get("breach_findings", [])) * 0.5

        # Account removals: 15 min each
        estimated_hours += len(findings.get("username_findings", [])) * 0.25

        # Email removals: 1 hour each
        estimated_hours += len(findings.get("email_findings", [])) * 1

        # Phone removals: 1 hour each
        estimated_hours += len(findings.get("phone_findings", [])) * 1

        # Determine difficulty
        if total_actions > 20:
            difficulty = "Complex - recommend professional service"
        elif total_actions > 10:
            difficulty = "Moderate - can be done independently"
        else:
            difficulty = "Simple - DIY cleanup feasible"

        return {
            "total_actions": total_actions,
            "estimated_hours": round(estimated_hours, 1),
            "difficulty_assessment": difficulty,
            "phases": [
                {
                    "phase": 1,
                    "name": "Critical Security (Breaches)",
                    "actions": len(findings.get("breach_findings", [])),
                    "estimated_time": f"{len(findings.get('breach_findings', [])) * 0.5} hours"
                },
                {
                    "phase": 2,
                    "name": "High-Risk Platform Removal",
                    "actions": len([f for f in findings.get("username_findings", []) if f.get("risk_level") == "high"]),
                    "estimated_time": "1-2 hours"
                },
                {
                    "phase": 3,
                    "name": "Contact Info Removal",
                    "actions": len(findings.get("email_findings", [])) + len(findings.get("phone_findings", [])),
                    "estimated_time": "2-4 hours"
                },
                {
                    "phase": 4,
                    "name": "General Cleanup",
                    "actions": len(findings.get("username_findings", [])) + len(findings.get("social_profiles", [])),
                    "estimated_time": "1-3 hours"
                }
            ]
        }

    def _assess_vulnerabilities(self, findings: Dict) -> Dict:
        """
        Assess specific vulnerabilities that could impact reputation.
        """

        vulnerabilities = []

        # Check for password exposure
        breaches_with_passwords = [
            b for b in findings.get("breach_findings", [])
            if b.get("passwords_exposed")
        ]

        if breaches_with_passwords:
            vulnerabilities.append({
                "type": "Password Exposure",
                "severity": "CRITICAL",
                "description": "Passwords exposed in data breaches",
                "impact": "Account takeover risk, identity theft",
                "recommendation": "Change passwords immediately, enable 2FA"
            })

        # Check for email exposure
        if len(findings.get("email_findings", [])) > 5:
            vulnerabilities.append({
                "type": "Email Oversharing",
                "severity": "HIGH",
                "description": "Email address widely distributed online",
                "impact": "Spam, phishing, social engineering attacks",
                "recommendation": "Request removal from listings, consider new email"
            })

        # Check for phone exposure
        if len(findings.get("phone_findings", [])) > 3:
            vulnerabilities.append({
                "type": "Phone Number Exposure",
                "severity": "HIGH",
                "description": "Phone number publicly accessible",
                "impact": "Spam calls, SIM swapping risk, doxxing",
                "recommendation": "Remove from public listings, consider number change"
            })

        # Check for reputation risk
        high_risk_platforms = [
            f for f in findings.get("username_findings", [])
            if f.get("risk_level") == "high"
        ]

        if high_risk_platforms:
            vulnerabilities.append({
                "type": "Reputation Risk",
                "severity": "HIGH",
                "description": f"Profiles on {len(high_risk_platforms)} high-risk platforms",
                "impact": "Professional reputation damage, background check issues",
                "recommendation": "Delete accounts immediately, request content removal"
            })

        # Check for excessive digital footprint
        total_profiles = len(findings.get("username_findings", [])) + len(findings.get("social_profiles", []))

        if total_profiles > 15:
            vulnerabilities.append({
                "type": "Excessive Digital Footprint",
                "severity": "MEDIUM",
                "description": f"Found {total_profiles} online profiles",
                "impact": "Privacy concerns, increased attack surface",
                "recommendation": "Consolidate accounts, delete unused profiles"
            })

        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "requires_immediate_action": any(v["severity"] == "CRITICAL" for v in vulnerabilities)
        }

    def generate_removal_request(self, finding: Dict) -> str:
        """
        Generate template email for removal request.
        """

        templates = {
            "email_removal": """
Subject: Request to Remove Personal Information

Dear Site Administrator,

I am writing to request the removal of my personal email address from your website.

Email Address: {email}
Page URL: {url}

I did not consent to having my email address listed publicly, and its presence on your site exposes me to spam and privacy risks.

Under GDPR Article 17 (Right to Erasure) and CCPA Section 1798.105, I have the right to request deletion of my personal information.

Please confirm removal within 30 days.

Thank you,
[Your Name]
""",
            "account_deletion": """
Subject: Account Deletion Request

Dear {platform} Support,

I am writing to request permanent deletion of my account.

Username: {username}
Account URL: {url}

Please delete all associated data including:
- Profile information
- Posts and comments
- Photos and media
- Email address

Please confirm deletion within 30 days as required by GDPR.

Thank you,
[Your Name]
""",
            "phone_removal": """
Subject: Remove Phone Number from Listing

Dear Administrator,

I am requesting removal of my phone number from your website.

Phone Number: {phone}
Page URL: {url}

I did not authorize this listing and request immediate removal.

Please confirm within 30 days.

Thank you,
[Your Name]
"""
        }

        # Determine which template to use
        if finding.get("type") == "public_mention" and "email" in finding:
            template = templates["email_removal"]
            return template.format(
                email=finding.get("email", ""),
                url=finding.get("url", "")
            )
        elif finding.get("type") == "phone_mention":
            template = templates["phone_removal"]
            return template.format(
                phone=finding.get("phone", ""),
                url=finding.get("url", "")
            )
        elif finding.get("platform"):
            template = templates["account_deletion"]
            return template.format(
                platform=finding.get("platform", ""),
                username=finding.get("username", ""),
                url=finding.get("url", "")
            )

        return "No template available for this finding type."

    def generate_cleanup_report(self, findings: Dict, analysis: Dict) -> str:
        """
        Generate comprehensive PDF-ready cleanup report.
        """

        report = f"""
DIGITAL FOOTPRINT ANALYSIS REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

===============================================
EXECUTIVE SUMMARY
===============================================

Risk Score: {analysis['risk_score']}/100
Risk Level: {analysis['risk_level']}

Total Findings: {sum(len(v) if isinstance(v, list) else 0 for v in findings.values())}
Critical Actions Required: {len([a for a in analysis['prioritized_actions'] if a.get('urgency') == 'IMMEDIATE'])}

===============================================
FINDINGS BREAKDOWN
===============================================

Data Breaches: {len(findings.get('breach_findings', []))}
Username Exposure: {len(findings.get('username_findings', []))}
Email Exposure: {len(findings.get('email_findings', []))}
Phone Exposure: {len(findings.get('phone_findings', []))}
Social Profiles: {len(findings.get('social_profiles', []))}

===============================================
VULNERABILITIES
===============================================

"""

        for vuln in analysis.get("vulnerability_assessment", {}).get("vulnerabilities", []):
            report += f"""
{vuln['type']} - {vuln['severity']}
Description: {vuln['description']}
Impact: {vuln['impact']}
Recommendation: {vuln['recommendation']}
"""

        report += f"""
===============================================
PRIORITIZED ACTION PLAN
===============================================

Estimated Cleanup Time: {analysis['cleanup_estimate']['estimated_hours']} hours
Difficulty: {analysis['cleanup_estimate']['difficulty_assessment']}

"""

        for idx, action in enumerate(analysis['prioritized_actions'][:10], 1):
            report += f"""
{idx}. [{action['urgency']}] {action['action']}
   Category: {action['category']}
   Details: {action['details']}
   Time: {action.get('estimated_time', 'Unknown')}

"""

        report += """
===============================================
RECOMMENDATIONS
===============================================

1. Change all passwords immediately (especially for breached accounts)
2. Enable two-factor authentication on all accounts
3. Remove high-risk profiles first
4. Request removal of public contact information
5. Consolidate and delete unused accounts
6. Review social media privacy settings
7. Consider identity monitoring service
8. Regularly audit digital footprint (quarterly)

===============================================
END OF REPORT
===============================================
"""

        return report
