"""
LLM Client for interacting with various LLM providers
"""
import logging
from typing import Optional
import openai
import anthropic

from config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM interactions"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        # Initialize appropriate client
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        elif self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        logger.info(f"LLM client initialized: {self.provider} / {self.model}")

    async def extract_structured_data(self, prompt: str) -> str:
        """
        Extract structured data using LLM

        Args:
            prompt: The extraction prompt

        Returns:
            JSON string with extracted data
        """
        try:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            logger.debug(f"LLM response received ({len(response)} chars)")
            return response

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}", exc_info=True)
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a expert data extraction assistant. You extract structured data from text and return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}  # Force JSON mode
        )

        return response.choices[0].message.content

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="You are a expert data extraction assistant. You extract structured data from text and return only valid JSON.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    async def validate_data(self, data_json: str) -> dict:
        """
        Validate extracted data using LLM

        Returns validation results with suggestions for improvements
        """
        prompt = f"""Review this extracted tax data for accuracy and completeness:

{data_json}

Return a JSON object with:
- is_valid: boolean
- completeness_score: 0-100
- confidence_score: 0-100
- issues: list of any problems found
- suggestions: list of improvements

Return ONLY valid JSON."""

        response = await self.extract_structured_data(prompt)
        import json
        return json.loads(response)
