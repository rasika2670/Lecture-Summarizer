from flask import Flask, request, jsonify
import os
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Create an uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    # Save the file locally for processing
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # Extract audio from video file if the uploaded file is a video
        audio_file_path = extract_audio(file_path)

        # Load the audio file using pydub
        audio = AudioSegment.from_file(audio_file_path)

        # Apply noise cancellation (convert to mono)
        audio = audio.set_channels(1)

        # Export the cleaned audio to a temporary file
        cleaned_file_path = os.path.join(UPLOAD_FOLDER, 'cleaned_audio.wav')
        audio.export(cleaned_file_path, format='wav')  # Export as WAV

        # Transcription logic
        r = sr.Recognizer()
        with sr.AudioFile(cleaned_file_path) as source:
            audio_data = r.record(source)  # Read the audio file
            transcription = r.recognize_google(audio_data)  # Transcribe audio
            return jsonify({'transcription': transcription})  # Return transcription

    except sr.UnknownValueError:
        return jsonify({'error': 'Speech Recognition could not understand audio.'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Could not request results from Google Speech Recognition service; {e}'}), 500
    except Exception as e:
        print(f"Error during transcription: {e}")  # Log the error for debugging
        return jsonify({'error': f'Error: Unable to transcribe the audio. {str(e)}'}), 500

def extract_audio(file_path):
    """Extract audio from video file if necessary."""
    if file_path.endswith(('.mp4', '.avi', '.mov')):
        audio_file_path = os.path.join(UPLOAD_FOLDER, 'extracted_audio.wav')
        video_clip = VideoFileClip(file_path)
        video_clip.audio.write_audiofile(audio_file_path)  # Extract audio and save as WAV
        video_clip.close()
        return audio_file_path
    return file_path  # If it's an audio file, use it directly

if __name__ == '__main__':
    app.run(debug=True)
