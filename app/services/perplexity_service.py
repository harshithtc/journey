import time
import json
from typing import Optional
from fastapi import HTTPException
from openai import OpenAI
from app.config import PERPLEXITY_API_KEY
from app.services.logging_config import setup_logging

logger = setup_logging()
client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

def safe_perplexity_call(prompt: str, model: str = "sonar-pro", retries: int = 3, delay: int = 2) -> str:
    """
    Make a safe call to Perplexity API with error handling and retries
    """
    for attempt in range(retries):
        try:
            logger.info("Making Perplexity API call", extra={"attempt": attempt + 1, "model": model})
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            
            result = response.choices[0].message.content
            logger.info("Perplexity API call successful", extra={"response_length": len(result)})
            return result
            
        except Exception as e:
            error_str = str(e)
            logger.error("Perplexity API call failed", extra={
                "attempt": attempt + 1,
                "error": error_str,
                "retries_left": retries - attempt - 1
            })
            
            # Handle rate limiting (429)
            if "429" in error_str or "rate limit" in error_str.lower():
                if attempt < retries - 1:
                    wait_time = delay * (2 ** attempt)  # exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=429, 
                        detail="API rate limit exceeded. Please try again later."
                    )
            
            # Handle other API errors
            if attempt == retries - 1:
                logger.error("All Perplexity API attempts failed")
                raise HTTPException(
                    status_code=500,
                    detail="External API service temporarily unavailable. Please try again later."
                )
    
    # This shouldn't be reached, but just in case
    raise HTTPException(status_code=500, detail="Unexpected error in API service")

def safe_itinerary_call(system_msg: str, user_prompt: str) -> str:
    """
    Specialized call for itinerary planning with system + user messages
    """
    try:
        logger.info("Making itinerary API call")
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0,
        )
        
        result = response.choices[0].message.content
        logger.info("Itinerary API call successful")
        return result
        
    except Exception as e:
        logger.error("Itinerary API call failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to generate travel itinerary")
