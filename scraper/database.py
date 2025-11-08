"""
Database client for scraper service

Connects to shared PostgreSQL database to save and retrieve tax data
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json

from config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Client for database operations"""

    def __init__(self):
        self.connection_string = settings.DATABASE_URL

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)

    async def save_tax_data(
        self,
        state: str,
        county: str,
        tax_data: Dict[str, Any]
    ) -> int:
        """
        Save tax data to database

        Creates a new version of tax data for the jurisdiction

        Returns:
            ID of saved tax data record
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get state and county IDs
            cursor.execute(
                "SELECT id FROM api_state WHERE code = %s",
                (state.upper(),)
            )
            state_result = cursor.fetchone()

            if not state_result:
                logger.error(f"State {state} not found in database")
                raise ValueError(f"State {state} not found")

            state_id = state_result[0]

            cursor.execute(
                "SELECT id FROM api_county WHERE state_id = %s AND name = %s",
                (state_id, county)
            )
            county_result = cursor.fetchone()

            if not county_result:
                logger.error(f"County {county} not found in database")
                raise ValueError(f"County {county}, {state} not found")

            county_id = county_result[0]

            # Get current max version
            cursor.execute(
                """
                SELECT COALESCE(MAX(version), 0) as max_version
                FROM api_taxdata
                WHERE state_id = %s AND county_id = %s
                """,
                (state_id, county_id)
            )
            max_version = cursor.fetchone()[0]
            new_version = max_version + 1

            # Mark all existing versions as not current
            cursor.execute(
                """
                UPDATE api_taxdata
                SET is_current = FALSE
                WHERE state_id = %s AND county_id = %s
                """,
                (state_id, county_id)
            )

            # Insert new tax data
            cursor.execute(
                """
                INSERT INTO api_taxdata (
                    state_id, county_id, version, is_current,
                    data_completeness, scraper_confidence,
                    data, effective_date, sources, notes,
                    created_at, updated_at, last_verified
                ) VALUES (
                    %s, %s, %s, TRUE,
                    %s, %s,
                    %s, %s, %s, %s,
                    NOW(), NOW(), NOW()
                )
                RETURNING id
                """,
                (
                    state_id,
                    county_id,
                    new_version,
                    tax_data.get('data_completeness', 0),
                    tax_data.get('scraper_confidence', 0),
                    Json(tax_data),
                    tax_data.get('effective_date', datetime.utcnow().strftime('%Y-%m-%d')),
                    Json(tax_data.get('sources', [])),
                    tax_data.get('notes', '')
                )
            )

            tax_data_id = cursor.fetchone()[0]

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Saved tax data for {county}, {state} (ID: {tax_data_id}, Version: {new_version})")

            return tax_data_id

        except Exception as e:
            logger.error(f"Failed to save tax data: {str(e)}", exc_info=True)
            raise

    def get_tax_data(self, state: str, county: str) -> Optional[Dict[str, Any]]:
        """
        Get current tax data for a jurisdiction

        Returns:
            Tax data dict or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT td.*
                FROM api_taxdata td
                JOIN api_state s ON td.state_id = s.id
                JOIN api_county c ON td.county_id = c.id
                WHERE s.code = %s AND c.name = %s AND td.is_current = TRUE
                """,
                (state.upper(), county)
            )

            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                # Convert to dict and handle JSON fields
                data = dict(result)
                data['last_verified'] = data['last_verified'].isoformat()
                return data

            return None

        except Exception as e:
            logger.error(f"Failed to get tax data: {str(e)}", exc_info=True)
            return None

    def get_total_count(self) -> int:
        """Get total number of jurisdictions scraped"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(DISTINCT (state_id, county_id))
                FROM api_taxdata
                WHERE is_current = TRUE
                """
            )

            count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Failed to get total count: {str(e)}")
            return 0

    def get_avg_completeness(self) -> float:
        """Get average data completeness score"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT AVG(data_completeness)
                FROM api_taxdata
                WHERE is_current = TRUE
                """
            )

            result = cursor.fetchone()[0]
            avg = float(result) if result else 0.0

            cursor.close()
            conn.close()

            return round(avg, 2)

        except Exception as e:
            logger.error(f"Failed to get avg completeness: {str(e)}")
            return 0.0

    def get_avg_confidence(self) -> float:
        """Get average confidence score"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT AVG(scraper_confidence)
                FROM api_taxdata
                WHERE is_current = TRUE
                """
            )

            result = cursor.fetchone()[0]
            avg = float(result) if result else 0.0

            cursor.close()
            conn.close()

            return round(avg, 2)

        except Exception as e:
            logger.error(f"Failed to get avg confidence: {str(e)}")
            return 0.0

    def get_stale_count(self) -> int:
        """Get count of stale data (older than expiry days)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            expiry_date = datetime.utcnow() - timedelta(days=settings.CACHE_EXPIRY_DAYS)

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM api_taxdata
                WHERE is_current = TRUE AND last_verified < %s
                """,
                (expiry_date,)
            )

            count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Failed to get stale count: {str(e)}")
            return 0
