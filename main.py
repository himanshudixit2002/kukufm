"""
Interactive Audio Quest - Main Application
Flask API to serve scenes and handle routes
"""
import os
import json
import uuid
import tempfile
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, render_template

# Import our custom modules
from story.story_engine import generate_scene, get_start_scene
from story.emotion_detector import detect_emotion
from audio.tts_engine import generate_scene_audio, text_to_speech_demo
from audio.stt_engine import get_text_from_audio, process_voice_command
from firebase.firebase_handler import FirebaseHandler

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize Firebase handler
firebase = FirebaseHandler()

# Ensure audio directory exists
os.makedirs('static/audio', exist_ok=True)

def load_sample_story():
    """Load the sample story from the JSON file"""
    try:
        with open('sample_data/sample_story.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sample story: {e}")
        return None

# Global variable to store the sample story
sample_story = load_sample_story()

@app.route('/')
def index():
    """Root endpoint - serves the web UI"""
    return render_template('index.html')

@app.route('/audio_test')
def audio_test():
    """Audio test page to diagnose audio issues"""
    return render_template('audio_test.html')

@app.route('/api')
def api_index():
    """API root endpoint - welcome message"""
    return jsonify({
        "message": "Welcome to the Interactive Audio Quest API",
        "endpoints": {
            "/start_story": "Start a new story",
            "/next_scene": "Get the next scene based on choice",
            "/voice_input": "Process voice input",
            "/save_progress": "Save user progress",
            "/get_state": "Get user state"
        }
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files - with specific headers for audio streaming"""
    response = send_from_directory('static/audio', filename)
    response.headers['Content-Type'] = 'audio/mpeg'
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@app.route('/start_story', methods=['GET'])
def start_story():
    """Start a new story from the first scene"""
    user_id = request.args.get('user_id', str(uuid.uuid4()))
    use_sample = request.args.get('use_sample', 'true').lower() == 'true'
    
    if use_sample and sample_story:
        first_scene_id = list(sample_story["scenes"].keys())[0]
        scene_data = sample_story["scenes"][first_scene_id]
    else:
        scene_data = get_start_scene()
    
    if not scene_data:
        print("Failed to load scene data.")
        return jsonify({"error": "Failed to load scene data."}), 500
    
    audio_paths = generate_scene_audio(scene_data)
    
    scene_data["audio"] = {
        "narrative": f"/audio/{os.path.basename(audio_paths['narrative'])}" if audio_paths.get('narrative') else None,
        "choices": {}
    }
    
    for i, choice in enumerate(scene_data.get("choices", [])):
        audio_key = f"choice_{i+1}"
        if audio_key in audio_paths and audio_paths[audio_key]:
            scene_data["audio"]["choices"][choice["id"]] = f"/audio/{os.path.basename(audio_paths[audio_key])}"
    
    firebase.save_user_progress(user_id, scene_data['scene_id'])
    
    firebase.log_metrics(user_id, {
        "action": "start_story",
        "scene_id": scene_data['scene_id'],
        "use_sample": use_sample
    })
    
    return jsonify({
        "user_id": user_id,
        "scene": scene_data
    })

@app.route('/next_scene', methods=['POST'])
def next_scene():
    """Get the next scene based on user choice"""
    data = request.json
    
    # Log incoming request data for debugging
    print(f"Received request data for next_scene: {data}")
    
    if not data or not data.get('user_id') or not data.get('choice_id'):
        return jsonify({
            "error": "Missing required parameters",
            "required": ["user_id", "choice_id"],
            "optional": ["scene_id", "use_sample", "emotion"]
        }), 400
    
    user_id = data['user_id']
    choice_id = data['choice_id']
    scene_id = data.get('scene_id')
    use_sample = data.get('use_sample', True)
    emotion = data.get('emotion')
    
    if not scene_id:
        user_state = firebase.get_user_state(user_id)
        scene_id = user_state.get('current_scene', 'start')
    
    if use_sample and sample_story:
        try:
            current_scene = sample_story["scenes"].get(scene_id)
            if not current_scene:
                return jsonify({"error": f"Scene {scene_id} not found in sample story"}), 404
                
            next_scene_id = None
            for choice in current_scene.get("choices", []):
                if choice["id"] == choice_id:
                    next_scene_id = choice.get("next_scene")
                    break
            
            if not next_scene_id:
                return jsonify({"error": f"Choice {choice_id} not found in scene {scene_id}"}), 404
                
            scene_data = sample_story["scenes"].get(next_scene_id)
            if not scene_data:
                return jsonify({"error": f"Next scene {next_scene_id} not found in sample story"}), 404
        except Exception as e:
            print(f"Error processing sample story: {str(e)}")
            return jsonify({"error": f"Error processing sample story: {str(e)}"}), 500
    else:
        # This would use the Gemini API in a full implementation
        previous_scene_summary = current_scene["narrative"] if current_scene else ""
        scene_data = generate_scene(previous_scene_summary, choice_id, emotion)
    
    audio_paths = generate_scene_audio(scene_data)
    
    scene_data["audio"] = {
        "narrative": f"/audio/{os.path.basename(audio_paths['narrative'])}" if audio_paths.get('narrative') else None,
        "choices": {}
    }
    
    for i, choice in enumerate(scene_data.get("choices", [])):
        audio_key = f"choice_{i+1}"
        if audio_key in audio_paths and audio_paths[audio_key]:
            scene_data["audio"]["choices"][choice["id"]] = f"/audio/{os.path.basename(audio_paths[audio_key])}"
    
    firebase.save_user_progress(user_id, scene_data['scene_id'])
    firebase.save_choice(user_id, scene_id, {
        "id": choice_id,
        "text": "Unknown choice"  # This would come from the current_scene in a full implementation
    })
    
    firebase.log_metrics(user_id, {
        "action": "next_scene",
        "previous_scene": scene_id,
        "choice_id": choice_id,
        "new_scene": scene_data['scene_id'],
        "emotion": emotion
    })
    
    return jsonify({
        "user_id": user_id,
        "scene": scene_data
    })

@app.route('/test_audio')
def test_audio():
    """Test the TTS system and return a demo audio URL"""
    result = text_to_speech_demo()
    return jsonify({"message": result, "audio_url": "/audio/demo.mp3"})

# Additional routes...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
