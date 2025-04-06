"""
Emotion Detector Module - Detects emotional tone using Gemini
"""
import os
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
            print(f"Error initializing Gemini model for emotion detection: {e}")
            return None

def detect_emotion(text_input):
    """
    Detect the emotional tone from user text input
    
    Args:
        text_input (str): The text to analyze for emotional content
        
    Returns:
        str: Detected emotion (happy, scared, curious, neutral, etc.)
    """
    if not text_input or text_input.strip() == "":
        return "neutral"
    
    model = init_gemini()
    if model is None:
        print("Falling back to default emotion: neutral")
        return "neutral"
    
    prompt = f"""
    Analyze the following text and determine the primary emotional state expressed.
    Classify the emotion as one of the following: happy, sad, angry, scared, curious, excited, confused, neutral, or surprised.
    
    Text: "{text_input}"
    
    Return only the emotion name, with no additional text or explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        detected_emotion = response.text.strip().lower()
        
        # Validate that the response is one of our expected emotions
        valid_emotions = ["happy", "sad", "angry", "scared", "curious", 
                         "excited", "confused", "neutral", "surprised"]
        
        if detected_emotion in valid_emotions:
            return detected_emotion
        else:
            return "neutral"
            
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return "neutral"

def get_emotion_prompt_modifier(emotion):
    """
    Get a prompt modifier based on the detected emotion
    
    Args:
        emotion (str): The detected emotion
        
    Returns:
        str: A prompt modifier to guide story generation
    """
    emotion_modifiers = {
        "happy": "Make the scene uplifting and positive, with hopeful elements.",
        "sad": "Add melancholic elements to the scene, with a touch of hope.",
        "angry": "Add intensity to the scene with opportunities to overcome challenges.",
        "scared": "Soften the tension slightly while maintaining the adventure atmosphere.",
        "curious": "Add more mysteries and discoverable elements to the scene.",
        "excited": "Amplify the adventure elements with thrilling discoveries.",
        "confused": "Provide clearer explanations and simpler choices.",
        "neutral": "Maintain a balanced tone with equal elements of mystery and clarity.",
        "surprised": "Add unexpected elements that capitalize on the user's sense of wonder."
    }
    
    return emotion_modifiers.get(emotion, emotion_modifiers["neutral"])
