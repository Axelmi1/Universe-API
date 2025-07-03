import json
import logging
import os
import time
from typing import Any, Dict, Optional

import openai
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables only once if not already loaded
if not openai.api_key:
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Logging configuration for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ask_llm(
    prompt: str,
    max_tokens: int = 800,
    retry_count: int = 2,
    response_schema: Optional[Dict] = None,
    force_json: bool = False,
) -> Dict[str, Any]:
    """
    Professional LLM client with optional native JSON mode for guaranteed JSON output
    """
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    for attempt in range(retry_count + 1):
        try:
            # Enhanced prompt with JSON requirements
            enhanced_prompt = f"""
{prompt}

CRITICAL: Return ONLY valid JSON matching the required schema exactly. 
No markdown, no explanations, no code blocks - just pure JSON.
"""

            messages = [
                {
                    "role": "system",
                    "content": "You are a professional health and wellness AI that provides accurate, evidence-based recommendations. Always return valid JSON responses that match the required schema exactly.",
                },
                {"role": "user", "content": enhanced_prompt},
            ]

            if force_json:
                # Native JSON mode - guaranteed JSON output
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.25,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content
                return json.loads(content)
            else:
                # Fallback method with regex parsing
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"},  # Native JSON mode
                    temperature=0.3,
                    max_tokens=max_tokens,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                )

                content = resp.choices[0].message.content.strip()
                logger.info(
                    f"LLM response received (attempt {attempt + 1}, tokens: ~{len(content)//4})"
                )

                # Parse JSON directly - no regex needed with JSON mode
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"JSON parsing failed despite JSON mode (attempt {attempt + 1}): {str(e)}"
                    )
                    raise e

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed (attempt {attempt + 1}): {str(e)}")
            if attempt == retry_count:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "JSON parsing failed after retries",
                        "json_error": str(e),
                        "attempt": attempt + 1,
                        "suggestion": "Please try again or contact support",
                    },
                )
            time.sleep(0.5)

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI service temporarily unavailable",
                    "message": "Please try again in a few seconds",
                },
            )

        except Exception as e:
            logger.error(f"Unexpected error in ask_llm: {str(e)}")
            if attempt == retry_count:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Internal service error",
                        "message": "An unexpected error occurred. Please contact support if this persists.",
                    },
                )
            time.sleep(0.5)
