"""
Text-to-Speech Engine Module - Converts scene text to speech

This module provides functionality to convert text to speech and save
audio files using both local (pyttsx3) and internet-based (gTTS) methods.
"""
import os
import threading
import requests
import tempfile
import pyttsx3
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
from urllib.parse import urlparse

# Global lock to ensure only one TTS operation runs at a time
tts_lock = threading.Lock()

def generate_audio(scene_text, scene_id, output_dir="static/audio", use_online=True):
    """
    Generate audio file from scene text - with option to use online TTS
    
    Args:
        scene_text (str): The text to convert to speech
        scene_id (str): Scene ID to use in the filename
        output_dir (str): Directory to save the audio file
        use_online (bool): Whether to use online TTS (True) or local TTS (False)
        
    Returns:
        str: Path to the generated audio file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare output path
    output_path = os.path.join(output_dir, f"{scene_id}.mp3")
    
    # Check if file already exists - if so, just return the path
    if os.path.exists(output_path):
        return output_path
    
    # Choose TTS method based on parameter
    if use_online and GTTS_AVAILABLE:
        # Use Google TTS (requires internet)
        try:
            return generate_online_audio(scene_text, output_path)
        except Exception as e:
            print(f"Online TTS failed: {e}. Falling back to local TTS.")
            return generate_local_audio(scene_text, output_path)
    else:
        # Use local pyttsx3
        return generate_local_audio(scene_text, output_path)

def generate_online_audio(text, output_path):
    """
    Generate audio using Google's Text-to-Speech API
    
    Args:
        text (str): The text to convert to speech
        output_path (str): Path to save the audio file
        
    Returns:
        str: Path to the generated audio file
    """
    try:
        if not GTTS_AVAILABLE:
            raise ImportError("gTTS is not installed. Run 'pip install gtts' to use online TTS.")
            
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error generating online audio: {e}")
        raise

def generate_local_audio(scene_text, output_path):
    """
    Generate audio using local pyttsx3 engine
    
    Args:
        scene_text (str): The text to convert to speech
        output_path (str): Path to save the audio file
        
    Returns:
        str: Path to the generated audio file
    """
    # Generate in a separate thread
    tts_thread = threading.Thread(
        target=_generate_audio_threaded,
        args=(scene_text, output_path)
    )
    tts_thread.start()
    
    return output_path

def _generate_audio_threaded(scene_text, output_path):
    """
    Thread worker function to generate audio locally
    
    Args:
        scene_text (str): The text to convert to speech
        output_path (str): Path to save the audio file
    """
    try:
        with tts_lock:  # Ensure only one TTS operation at a time
            # Initialize a new engine each time
            engine = pyttsx3.init()
            
            # Set properties
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Get available voices and set a voice
            voices = engine.getProperty('voices')
            if voices:
                # Try to find a female voice (often index 1)
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    engine.setProperty('voice', voices[0].id)
            
            # Save to file
            engine.save_to_file(scene_text, output_path)
            engine.runAndWait()
            
            # Clean up
            engine.stop()
            
    except Exception as e:
        print(f"Error generating audio locally: {e}")

def use_audio_from_url(url, scene_id, output_dir="static/audio"):
    """
    Download audio from URL and save to local file
    
    Args:
        url (str): URL of the audio file to download
        scene_id (str): Scene ID to use in the filename
        output_dir (str): Directory to save the audio file
        
    Returns:
        str: Path to the downloaded audio file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract file extension from URL or default to .mp3
    parsed_url = urlparse(url)
    path = parsed_url.path
    extension = os.path.splitext(path)[1]
    if not extension:
        extension = '.mp3'
    
    # Prepare output path
    output_path = os.path.join(output_dir, f"{scene_id}{extension}")
    
    # Check if file already exists - if so, just return the path
    if os.path.exists(output_path):
        return output_path
    
    # Download the file
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
    except Exception as e:
        print(f"Error downloading audio from URL: {e}")
        return None

def generate_scene_audio(scene_data, output_dir="static/audio", use_online=True):
    """
    Generate audio files for a complete scene
    
    Args:
        scene_data (dict): The scene data with narrative and choices
        output_dir (str): Directory to save the audio files
        use_online (bool): Whether to use online TTS
        
    Returns:
        dict: Paths to the generated audio files
    """
    audio_paths = {}
    
    # Generate audio for the narrative
    if "narrative" in scene_data:
        narrative_path = generate_audio(
            scene_data["narrative"], 
            f"{scene_data['scene_id']}_narrative", 
            output_dir,
            use_online
        )
        audio_paths["narrative"] = narrative_path
    
    # Generate audio for each choice
    for i, choice in enumerate(scene_data.get("choices", [])):
        choice_text = choice["text"]
        choice_id = choice["id"]
        
        choice_path = generate_audio(
            choice_text,
            f"{scene_data['scene_id']}_{choice_id}",
            output_dir,
            use_online
        )
        audio_paths[f"choice_{i+1}"] = choice_path
    
    return audio_paths

def text_to_speech_demo():
    """A simple demo function to test TTS functionality"""
    try:
        # Use a temporary file for the demo
        temp_file = os.path.join("static/audio", "demo.mp3")
        os.makedirs("static/audio", exist_ok=True)
        
        demo_text = "Welcome to the Interactive Audio Quest. Your adventure awaits!"
        generate_audio(demo_text, "demo", use_online=GTTS_AVAILABLE)
        
        return "TTS demo queued successfully. Audio will be available at: " + temp_file
    except Exception as e:
        return f"TTS demo failed: {e}"

# Sample premium audio URLs - for demonstration purposes only
# In a real implementation, these would be actual URLs to audio files
PREMIUM_AUDIO_LIBRARY = {
    "forest_ambience": "https://example.com/audio/forest_ambience.mp3",
    "mystery_theme": "https://example.com/audio/mystery_theme.mp3",
    "magic_spell": "https://example.com/audio/magic_spell.mp3"
}
