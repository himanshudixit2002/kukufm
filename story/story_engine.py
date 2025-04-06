"""
Story Engine Module - Handles Gemini-based story generation
"""
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_gemini():
    """Initialize the Gemini API with API key from environment variables"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    # Use gemini-1.5-pro or other available models with fallbacks
    try:
        # First try newer model version
        return genai.GenerativeModel('gemini-1.5-pro')
    except Exception:
        try:
            # Fall back to older version
            return genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            return None

def generate_scene(previous_scene_summary=None, user_choice=None, emotion=None):
    """
    Generate a new scene based on previous scene and user choice
    
    Args:
        previous_scene_summary (str): Summary of the previous scene
        user_choice (dict): The choice made by the user
        emotion (str): Detected emotion from the user's voice
        
    Returns:
        dict: JSON object containing the new scene
    """
    model = init_gemini()
    if model is None:
        print("Falling back to default scene generation.")
        return create_fallback_scene()
    
    # Build the prompt based on available information
    prompt = "Generate an interactive audio quest scene in JSON format."
    
    if previous_scene_summary:
        prompt += f"\n\nPrevious scene summary: {previous_scene_summary}"
    
    if user_choice:
        prompt += f"\n\nUser chose: {user_choice['text']}"
    
    if emotion:
        prompt += f"\n\nUser's emotional state: {emotion}. Adapt the scene to this emotion."
    
    prompt += """
    The scene should be detailed, immersive, and include ambient sound descriptions.
    Return the scene in this JSON format:
    {
      "scene_id": "unique_id",
      "title": "Scene Title",
      "narrative": "Detailed scene description that can be read aloud...",
      "ambience": "Description of background sounds",
      "choices": [
        {"id": "choice1_id", "text": "First choice description"},
        {"id": "choice2_id", "text": "Second choice description"},
        {"id": "choice3_id", "text": "Optional third choice description"}
      ]
    }
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        try:
            if "```json" in response_text and "```" in response_text.split("```json")[1]:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                scene_data = json.loads(json_str)
            else:
                scene_data = json.loads(response_text)
                
            return scene_data
        except json.JSONDecodeError:
            return create_fallback_scene()
            
    except Exception as e:
        print(f"Error generating scene: {e}")
        return create_fallback_scene()

def create_fallback_scene():
    """Create a fallback scene in case of API failure"""
    return {
        "scene_id": "fallback_scene",
        "title": "Continuing Your Journey",
        "narrative": "As you continue on your journey, you notice the path diverges ahead. What would you like to do?",
        "ambience": "Gentle wind rustling through leaves",
        "choices": [
            {"id": "path_left", "text": "Take the path to the left"},
            {"id": "path_right", "text": "Take the path to the right"},
            {"id": "wait", "text": "Wait and observe"}
        ]
    }

def get_start_scene():
    """Get the first scene of a story"""
    model = init_gemini()
    
    prompt = """
    Generate the first scene of an interactive audio quest adventure.
    The scene should be detailed, immersive, and include ambient sound descriptions.
    It should set up an intriguing beginning to a fantasy adventure.
    
    Return the scene in this JSON format:
    {
      "scene_id": "start",
      "title": "Beginning of the Journey",
      "narrative": "Detailed scene description that can be read aloud...",
      "ambience": "Description of background sounds",
      "choices": [
        {"id": "choice1_id", "text": "First choice description"},
        {"id": "choice2_id", "text": "Second choice description"},
        {"id": "choice3_id", "text": "Optional third choice description"}
      ]
    }
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        
        try:
            if "```json" in response_text and "```" in response_text.split("```json")[1]:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                scene_data = json.loads(json_str)
            else:
                scene_data = json.loads(response_text)
                
            return scene_data
        except json.JSONDecodeError:
            return {
                "scene_id": "start",
                "title": "The Whispering Forest",
                "narrative": "You stand at the edge of the Whispering Forest. The ancient trees sway gently, their leaves rustling with secrets older than time itself. A narrow path winds its way into the dense foliage, barely visible in the dappled sunlight. From somewhere deep within, you hear what sounds like distant voices carried on the breeze.",
                "ambience": "Rustling leaves, distant whispers, occasional bird calls",
                "choices": [
                    {"id": "enter_forest", "text": "Enter the forest and follow the path"},
                    {"id": "listen_carefully", "text": "Stand still and listen carefully to the whispers"},
                    {"id": "circle_perimeter", "text": "Circle around the perimeter to find another entrance"}
                ]
            }
    except Exception as e:
        print(f"Error generating start scene: {e}")
        return {
            "scene_id": "start",
            "title": "The Whispering Forest",
            "narrative": "You stand at the edge of the Whispering Forest. The ancient trees sway gently, their leaves rustling with secrets older than time itself. A narrow path winds its way into the dense foliage, barely visible in the dappled sunlight. From somewhere deep within, you hear what sounds like distant voices carried on the breeze.",
            "ambience": "Rustling leaves, distant whispers, occasional bird calls",
            "choices": [
                {"id": "enter_forest", "text": "Enter the forest and follow the path"},
                {"id": "listen_carefully", "text": "Stand still and listen carefully to the whispers"},
                {"id": "circle_perimeter", "text": "Circle around the perimeter to find another entrance"}
            ]
        }
