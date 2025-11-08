"""
Comprehensive unit tests for scraper agent
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from scraper_agent import ScraperAgent
from llm_client import LLMClient
from web_search import WebSearchClient


class TestScraperAgent:
    """Test suite for ScraperAgent"""

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results"""
        return [
            {
                "title": "Montgomery County MD Tax Rates",
                "url": "https://www.montgomerycountymd.gov/finance/tax",
                "snippet": "Property tax rate is 1.1234% for 2025"
            },
            {
                "title": "Maryland Transfer Tax",
                "url": "https://dat.maryland.gov/",
                "snippet": "State transfer tax is 0.5% and county rate varies"
            }
        ]

    @pytest.fixture
    def sample_tax_data(self):
        """Sample tax data"""
        return {
            "state": "MD",
            "county": "Montgomery",
            "effective_date": "2025-01-01",
            "data_completeness": 95,
            "scraper_confidence": 90,
            "property_tax": {
                "total_rate": 0.011234,
                "assessment_ratio": 100,
                "components": {
                    "county": 0.007,
                    "state": 0.001,
                    "municipality": 0.001,
                    "school": 0.002234
                }
            },
            "transfer_tax": {
                "state_rate": 0.005,
                "county_rate": 0.01
            },
            "recordation_tax": {
                "tiers": [
                    {"max_value": 500000, "rate": 0.0035}
                ]
            },
            "recording_fees": {
                "deed": {"flat": 50, "per_page": 5},
                "mortgage": {"flat": 80, "per_page": 5},
                "surcharge": 20
            },
            "insurance_estimate": {
                "base_premium_per_100k": 650
            },
            "sources": [
                "https://www.montgomerycountymd.gov/finance/"
            ]
        }

    def test_is_official_source(self):
        """Test official source validation"""
        agent = ScraperAgent()

        # Official sources
        assert agent._is_official_source("https://www.montgomerycountymd.gov/")
        assert agent._is_official_source("https://dat.maryland.gov/")
        assert agent._is_official_source("https://treasurer.example.us/")

        # Non-official sources
        assert not agent._is_official_source("https://zillow.com/")
        assert not agent._is_official_source("https://realtor.com/")
        assert not agent._is_official_source("https://example.com/")

    def test_deduplicate_sources(self):
        """Test source deduplication"""
        agent = ScraperAgent()

        sources = [
            {"url": "https://example.gov/page1", "title": "Title 1"},
            {"url": "https://example.gov/page1", "title": "Title 1 Duplicate"},
            {"url": "https://example.gov/page2", "title": "Title 2"},
            {"url": "https://example.us/page3", "title": "Title 3"},
        ]

        unique = agent._deduplicate_sources(sources)

        assert len(unique) == 3
        # Should prefer .gov
        assert unique[0]['url'] == "https://example.gov/page1"

    def test_calculate_completeness(self):
        """Test data completeness calculation"""
        agent = ScraperAgent()

        # Complete data
        complete_data = {
            "property_tax": {"total_rate": 0.01, "assessment_ratio": 100},
            "transfer_tax": {"state_rate": 0.005, "county_rate": 0.01},
            "recordation_tax": {"tiers": []},
            "recording_fees": {"deed": {}, "mortgage": {}},
            "insurance_estimate": {"base_premium_per_100k": 650}
        }

        score = agent._calculate_completeness(complete_data)
        assert score == 100

        # Incomplete data
        incomplete_data = {
            "property_tax": {"total_rate": 0.01}
        }

        score = agent._calculate_completeness(incomplete_data)
        assert score < 100

    def test_validate_numeric_values(self, sample_tax_data):
        """Test numeric validation doesn't raise errors for valid data"""
        agent = ScraperAgent()

        # Should not raise any exceptions
        agent._validate_numeric_values(sample_tax_data)

    @pytest.mark.asyncio
    async def test_find_official_sources(self):
        """Test finding official sources"""
        agent = ScraperAgent()

        with patch.object(agent.search_client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "title": "Official Site",
                    "url": "https://example.gov/",
                    "snippet": "Official government site"
                }
            ]

            sources = await agent._find_official_sources("MD", "Montgomery")

            assert len(sources) > 0
            assert all('.gov' in s['url'] or '.us' in s['url'] for s in sources)

    @pytest.mark.asyncio
    async def test_extract_tax_data(self, sample_search_results, sample_tax_data):
        """Test tax data extraction"""
        agent = ScraperAgent()

        with patch.object(agent.llm_client, 'extract_structured_data', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(sample_tax_data)

            result = await agent._extract_tax_data(
                "MD",
                "Montgomery",
                sample_search_results
            )

            assert result['state'] == 'MD'
            assert result['county'] == 'Montgomery'
            assert result['data_completeness'] >= 80

    @pytest.mark.asyncio
    async def test_validate_and_enrich(self, sample_tax_data):
        """Test data validation and enrichment"""
        agent = ScraperAgent()

        result = await agent._validate_and_enrich(
            sample_tax_data,
            "MD",
            "Montgomery"
        )

        assert 'state' in result
        assert 'county' in result
        assert 'effective_date' in result
        assert 'scraper_confidence' in result


class TestLLMClient:
    """Test suite for LLM Client"""

    @pytest.mark.asyncio
    async def test_llm_client_initialization(self):
        """Test LLM client can be initialized"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            client = LLMClient()
            assert client.provider in ['openai', 'anthropic']

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test structured data extraction"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            client = LLMClient()

            with patch.object(client, '_call_anthropic', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = '{"test": "data"}'

                result = await client.extract_structured_data("Test prompt")

                assert result == '{"test": "data"}'
                mock_call.assert_called_once()


class TestWebSearchClient:
    """Test suite for Web Search Client"""

    @pytest.mark.asyncio
    async def test_search_serpapi(self):
        """Test SerpAPI search"""
        client = WebSearchClient()

        with patch('serpapi.GoogleSearch') as mock_search:
            mock_instance = mock_search.return_value
            mock_instance.get_dict.return_value = {
                "organic_results": [
                    {
                        "title": "Test",
                        "link": "https://example.com",
                        "snippet": "Test snippet"
                    }
                ]
            }

            results = await client._search_serpapi("test query")

            assert len(results) == 1
            assert results[0]['title'] == 'Test'

    @pytest.mark.asyncio
    async def test_fetch_page_content(self):
        """Test fetching page content"""
        client = WebSearchClient()

        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <p>This is test content</p>
                <script>alert('test');</script>
            </body>
        </html>
        """

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.text = html_content
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            content = await client.fetch_page_content("https://example.com")

            assert "This is test content" in content
            assert "alert" not in content  # Script should be removed


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
