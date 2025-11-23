#!/usr/bin/env python3
"""
Cache Manager
Handles SQLite caching of search results
ONE JOB: Manage database operations for caching
"""

import sqlite3
import json
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta


class CacheManager:
    """
    Manages SQLite cache database for search results.
    Handles: caching, retrieval, expiration, cleanup.
    """

    def __init__(self, db_path: str = "database/search_cache.db"):
        """
        Initialize cache manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Search cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_hash TEXT UNIQUE NOT NULL,
                search_params TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')

        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_params TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _generate_search_hash(
        self,
        name: Optional[str],
        phone: Optional[str],
        address: Optional[str],
        email: Optional[str]
    ) -> str:
        """Generate unique hash for search parameters"""
        params = f"{name}|{phone}|{address}|{email}"
        return hashlib.md5(params.encode()).hexdigest()

    def check_cache(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        max_age_hours: int = 24
    ) -> Optional[Dict]:
        """
        Check if we have recent cached results for this search.

        Args:
            name, phone, address, email: Search parameters
            max_age_hours: Maximum age of cached results to accept

        Returns:
            Cached results dict or None if not found/expired
        """
        search_hash = self._generate_search_hash(name, phone, address, email)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT results FROM search_cache
            WHERE search_hash = ? AND expires_at > datetime('now')
        ''', (search_hash,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])

        return None

    def cache_results(self, results: Dict, cache_duration_hours: int = 24):
        """
        Cache search results for future use.

        Args:
            results: Search results to cache
            cache_duration_hours: How long to keep cached (default 24 hours)
        """
        search_params = results.get("search_params", {})
        search_hash = self._generate_search_hash(
            search_params.get("name"),
            search_params.get("phone"),
            search_params.get("address"),
            search_params.get("email")
        )

        expires_at = datetime.now() + timedelta(hours=cache_duration_hours)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache
                (search_hash, search_params, results, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                search_hash,
                json.dumps(search_params),
                json.dumps(results),
                expires_at
            ))

            conn.commit()

        finally:
            conn.close()

    def clear_old_cache(self, days: int = 7):
        """
        Remove cache entries older than specified days.

        Args:
            days: Delete entries older than this (0 = delete all)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM search_cache
            WHERE expires_at < datetime('now')
        ''')

        conn.commit()
        conn.close()

    def add_to_history(self, search_params: Dict):
        """
        Add search to history log.

        Args:
            search_params: Parameters used for this search
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO search_history (search_params)
                VALUES (?)
            ''', (json.dumps(search_params),))

            conn.commit()

        finally:
            conn.close()

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (total searches, cached results, etc.)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Count total searches from history
            cursor.execute('SELECT COUNT(*) FROM search_history')
            total_searches = cursor.fetchone()[0]

            # Count cached results (non-expired)
            cursor.execute("SELECT COUNT(*) FROM search_cache WHERE expires_at > datetime('now')")
            cached_results = cursor.fetchone()[0]

            return {
                "total_searches": total_searches,
                "cached_results": cached_results
            }

        finally:
            conn.close()
