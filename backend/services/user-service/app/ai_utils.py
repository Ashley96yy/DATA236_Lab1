import os
import httpx
import json
from typing import List, Dict, Any, Optional

class TavilyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"

    async def search_restaurants(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        
        payload = {
            "api_key": self.api_key,
            "query": f"restaurants recommendations for {query}",
            "search_depth": "basic",
            "max_results": 10
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, json=payload, timeout=10.0)
                response.raise_for_status()
                results = response.json().get("results", [])
                
                fetched_count = len(results)
                
                # Filtering logic
                whitelist = {
                    "restaurant", "cafe", "food", "dining", "menu", "cuisine", "eat", "drink", "bistro", 
                    "grill", "bar", "pub", "guide", "review", "tripadvisor", "yelp", "zomato", "maps",
                    "sushi", "pizza", "burger", "steak", "pasta", "bakery", "coffee", "breakfast", "lunch", "dinner",
                    "spots", "places", "tasty", "delicious", "eater", "michelin", "brunch", "local", "kitchen"
                }
                blacklist = {"python", "code", "tutorial", "stack overflow", "programming", "github", "npm", "install", "build", "developer", "api", "endpoint", "documentation"}
                
                restaurants = []
                for res in results:
                    title = res.get("title", "").lower()
                    description = res.get("content", "").lower()
                    url = res.get("url", "").lower()
                    
                    text_to_check = f"{title} {description} {url}"
                    
                    # Check blacklist first
                    if any(word in text_to_check for word in blacklist):
                        continue
                        
                    # Check whitelist
                    if any(word in text_to_check for word in whitelist):
                        restaurants.append({
                            "name": res.get("title", "Unknown Restaurant"),
                            "url": res.get("url"),
                            "description": res.get("content", ""),
                        })
                
                final_count = len(restaurants)
                filtered_count = fetched_count - final_count
                
                print(f"Tavily Fallback Stats: Fetched={fetched_count}, Filtered={filtered_count}, Passed={final_count}")
                
                # Limit to top 5
                return restaurants[:5]
            except Exception as e:
                print(f"Tavily search failed: {e}")
                return []

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return "I'm sorry, the Google AI API key is not configured. Please set GOOGLE_API_KEY."

        url = f"{self.base_url}?key={self.api_key}"
        
        # Construct the payload for Gemini API
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "response_mime_type": "application/json" if system_prompt and "JSON" in system_prompt else "text/plain"
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                # Extract the text from Gemini response
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                    return candidates[0]["content"]["parts"][0]["text"]
                
                return "I'm sorry, I couldn't generate a response at this time."
            except httpx.HTTPStatusError as e:
                print(f"Gemini API error: {e.response.text}")
                return f"I'm sorry, I encountered an error with the Gemini API (Status: {e.response.status_code})."
            except Exception as e:
                print(f"Gemini generation failed: {e}")
                return "I'm sorry, I encountered an unexpected error while generating a response."

# Singleton instances (or factory)
def get_tavily_client():
    enabled = os.getenv("TAVILY_ENABLED", "true").lower() == "true"
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not enabled or not api_key:
        return TavilyClient("") # Will return empty results
    return TavilyClient(api_key)

def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return GeminiClient(api_key, model)
