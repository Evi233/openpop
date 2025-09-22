import os
from openai import OpenAI
from typing import Union, List, Dict, Optional



class ContentModerator:
    """
    A class to handle content moderation using OpenAI's moderation API.
    Supports both text and image moderation with the omni-moderation-latest model.
    """
    
    def __init__(self, baseurl,api_key: Optional[str] = None):
        """
        Initialize the moderator with an optional API key.
        If no key is provided, will use OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = "text-moderation-stable"
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=self.api_key, base_url=baseurl)  # 使用全局 baseurl
    
    def _make_request(self, payload: Dict) -> Dict:
        """
        Make the API request using OpenAI SDK.
        
        Args:
            payload: The request payload
            
        Returns:
            Dict containing the API response
            
        Raises:
            Exception: If API request fails
        """
        try:
            response = self.client.moderations.create(**payload)
            return response.model_dump()
        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def moderate_text(self, text: str) -> Dict:
        """
        Moderate a single text input.
        
        Args:
            text: The text to moderate
            
        Returns:
            Dict containing moderation results with categories and scores
        """
        payload = {
            "model": self.model,
            "input": text
        }
        response = self._make_request(payload)
        return self._format_response(response)
    
    def moderate_image(self, image_url: str) -> Dict:
        """
        Moderate a single image input.
        
        Args:
            image_url: URL of the image to moderate
            
        Returns:
            Dict containing moderation results with categories and scores
        """
        payload = {
            "model": self.model,
            "input": [{
                "type": "image_url",
                "image_url": {"url": image_url}
            }]
        }
        response = self._make_request(payload)
        return self._format_response(response)
    
    def moderate_mixed(self, inputs: List[Union[str, Dict]]) -> Dict:
        """
        Moderate mixed text and image inputs.
        
        Args:
            inputs: List of either text strings or image dicts
                   Example: ["text", {"type": "image_url", "image_url": {"url": "..."}}]
                   
        Returns:
            Dict containing moderation results with categories and scores
        """
        payload = {
            "model": self.model,
            "input": inputs
        }
        response = self._make_request(payload)
        return self._format_response(response)
    
    def _format_response(self, response: Dict) -> Dict:
        """
        Format the raw API response into a more usable structure.
        
        Args:
            response: Raw API response dict
            
        Returns:
            Formatted dict with:
            - flagged: bool if any category was flagged
            - categories: dict of category flags
            - scores: dict of category scores
            - applied_types: dict showing which input types triggered each category
        """
        result = response["results"][0]
        return {
            "flagged": result["flagged"],
            "categories": result["categories"],
            "scores": result["category_scores"],
            "applied_types": result.get("category_applied_input_types", {})
        }

def is_content_safe(moderation_result: Dict, threshold: float = 0.5) -> bool:
    """
    Helper function to check if content is safe based on moderation results.
    
    Args:
        moderation_result: Result from ContentModerator methods
        threshold: Score threshold to consider unsafe (0-1)
        
    Returns:
        bool: True if no categories exceed threshold, False otherwise
    """
    for score in moderation_result["scores"].values():
        if score > threshold:
            return False
    return True
