# Interactive Audio Quest

A Python backend project for an Interactive Audio Quest App using the Gemini API. This application enables dynamic storytelling with audio capabilities and emotional adaptation.

## Features

- **Dynamic Story Generation**: Using Google's Gemini AI to create interactive narratives
- **Voice Interaction**: Text-to-speech and speech-to-text capabilities
- **Emotional Intelligence**: Story adaptation based on detected user emotions
- **Progress Tracking**: User state and choices saved with Firebase (or local fallback)
- **Sample Story**: "The Whispering Forest" adventure included

## Directory Structure

```
interactive_audio_quest/
├── .env                         # Environment variables with Gemini API key
├── main.py                      # Flask API for scenes and routes
├── requirements.txt             # Dependencies
├── story/
│   ├── story_engine.py         # Gemini-based story generation
│   ├── emotion_detector.py     # Detects emotional tone using Gemini
├── audio/
│   ├── tts_engine.py           # Text-to-speech conversion
│   ├── stt_engine.py           # Speech-to-text conversion
├── firebase/
│   └── firebase_handler.py     # User state, bookmarks, and metrics
├── sample_data/
│   └── sample_story.json       # Sample episode: "The Whispering Forest"
└── static/
    └── audio/                  # Directory for generated audio files
```

## Setup

1. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in the project root with:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   FIREBASE_KEY_PATH=path/to/firebase_key.json  # Optional
   ```

3. **Run the Application**:
   ```
   python main.py
   ```
   The API will be available at `http://localhost:8080`

## API Endpoints

- **GET /start_story**: Begin a new story adventure
  - Query params: `user_id` (optional), `use_sample` (boolean, optional)
  - Returns: Initial scene data with audio paths

- **POST /next_scene**: Progress to the next scene based on choice
  - Body (JSON): `user_id`, `choice_id`, `scene_id` (optional), `use_sample` (optional), `emotion` (optional)
  - Returns: Next scene data with audio paths

- **POST /voice_input**: Process voice input for choice selection
  - Form data: `user_id`, `scene_id`, `audio` (file), `available_choices` (JSON string, optional)
  - Returns: Matched choice, transcribed text, and detected emotion

- **POST /save_progress**: Save current user progress
  - Body (JSON): `user_id`, `scene_id`
  - Returns: Success status

- **GET /get_state**: Retrieve user state information
  - Query params: `user_id`
  - Returns: User state data

## Testing

### Test with curl

1. **Start a new story**:
   ```bash
   curl "http://localhost:8080/start_story"
   ```

2. **Get the next scene based on a choice**:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"user_id":"test_user","scene_id":"forest_entrance","choice_id":"enter_forest","use_sample":true}' http://localhost:8080/next_scene
   ```

3. **Get user state**:
   ```bash
   curl "http://localhost:8080/get_state?user_id=test_user"
   ```

## Offline Mode

If Firebase is not configured, the application automatically operates in offline mode, storing data in local JSON files under an `offline_data` directory.

## License

[MIT License](LICENSE)
