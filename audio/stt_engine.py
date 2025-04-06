"""
Speech-to-Text Engine Module - Converts speech to text
"""
import os
import speech_recognition as sr
from pathlib import Path

def get_text_from_audio(audio_path):
    """
    Convert speech in an audio file to text
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Extracted text from the audio or an error message
    """
    # Check if file exists
    if not os.path.isfile(audio_path):
        return "Error: Audio file not found"
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            
            # Record the audio
            audio_data = recognizer.record(source)
            
            # Use Google's Speech Recognition
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Error: Speech recognition could not understand audio"
    except sr.RequestError as e:
        return f"Error: Could not request results from service; {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

def process_voice_command(audio_path, available_choices=None):
    """
    Process a voice command and match it to an available choice
    
    Args:
        audio_path (str): Path to the audio file
        available_choices (list): List of available choice dictionaries
        
    Returns:
        dict: Matched choice or error message if no match found
    """
    if not available_choices:
        return {"error": "No available choices provided."}
        
    # Get text from audio
    text = get_text_from_audio(audio_path)
    
    if text.startswith("Error"):
        return {"error": text}
    
    # Simple matching algorithm - find choice with most words matching the transcribed text
    best_match = None
    max_matches = 0
    
    text_words = set(text.lower().split())
    
    for choice in available_choices:
        choice_words = set(choice["text"].lower().split())
        matches = len(text_words.intersection(choice_words))
        
        if matches > max_matches:
            max_matches = matches
            best_match = choice
    
    # If we have a reasonable match (at least one matching word)
    if max_matches > 0:
        return best_match
    else:
        return {"error": "Could not match voice command to any available choice"}

def mic_speech_to_text(timeout=5):
    """
    Convert speech from microphone to text
    
    Args:
        timeout (int): Maximum number of seconds to listen
        
    Returns:
        str: Extracted text from speech or an error message
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("Listening...")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            
            # Listen for speech
            audio_data = recognizer.listen(source, timeout=timeout)
            
            print("Recognizing...")
            # Use Google's Speech Recognition
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Error: Speech recognition could not understand audio"
    except sr.RequestError as e:
        return f"Error: Could not request results from service; {e}"
    except Exception as e:
        return f"Error processing speech: {e}"
