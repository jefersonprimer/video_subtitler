import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import uuid
import tempfile
import shutil
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import json
import time
from utils.video_processor import extract_audio, get_video_info, embed_subtitles
from utils.subtitle_generator import (
    generate_subtitles, srt_to_dict, dict_to_srt, 
    detect_subtitle_language, translate_subtitles
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'video_subtitler')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Import utilities are already included above

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['video']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Create a unique session ID and folder for this upload
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        video_path = os.path.join(session_folder, filename)
        file.save(video_path)
        
        session['video_filename'] = filename
        session['video_path'] = video_path
        
        try:
            # Extract audio from the video
            audio_path = os.path.join(session_folder, 'audio.wav')
            extract_audio(video_path, audio_path)
            
            # Generate subtitles using Whisper for better accuracy
            subtitles_path = os.path.join(session_folder, 'subtitles.srt')
            
            app.logger.info("Using Whisper base model for transcription")
            flash('Using Whisper for transcription. This may take a few minutes.', 'info')
            
            generate_subtitles(
                audio_path, 
                subtitles_path, 
                use_whisper=True,
                whisper_model="base"
            )
            
            # Save paths to session
            session['audio_path'] = audio_path
            session['subtitles_path'] = subtitles_path
            
            # Get video info
            video_info = get_video_info(video_path)
            session['video_info'] = video_info
            
            # Read SRT file and convert to JSON for editing
            subtitles_dict = srt_to_dict(subtitles_path)
            
            # Detect the language of the subtitles
            language_code = detect_subtitle_language(subtitles_dict)
            app.logger.info(f"Detected subtitle language: {language_code}")
            
            # Always translate to Brazilian Portuguese (pt-br) regardless of the source language
            # This is a key requirement for this application
            app.logger.info(f"Translating subtitles from {language_code} to pt-br (Brazilian Portuguese)")
            flash(f'Translating detected {language_code} speech to Brazilian Portuguese...', 'info')
            subtitles_dict = translate_subtitles(subtitles_dict, target_language='pt-br')
            
            # Save the translated subtitles back to the SRT file
            dict_to_srt(subtitles_dict, subtitles_path)
            
            flash('Subtitles automatically translated to Brazilian Portuguese.', 'success')
            
            session['subtitles'] = subtitles_dict
            
            return redirect(url_for('edit_subtitles'))
        
        except Exception as e:
            app.logger.error(f"Error processing video: {str(e)}")
            flash(f'Error processing video: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        return redirect(url_for('index'))

@app.route('/edit', methods=['GET'])
def edit_subtitles():
    if 'session_id' not in session or 'subtitles' not in session:
        flash('No video processing session found', 'warning')
        return redirect(url_for('index'))
    
    video_info = session.get('video_info', {})
    video_filename = session.get('video_filename', '')
    subtitles = session.get('subtitles', [])
    
    return render_template('edit.html', 
                          video_info=video_info,
                          video_filename=video_filename,
                          subtitles=subtitles)

@app.route('/save_subtitles', methods=['POST'])
def save_subtitles():
    if 'session_id' not in session:
        return json.dumps({'success': False, 'error': 'Session expired'}), 400
    
    try:
        subtitles_data = request.json
        session['subtitles'] = subtitles_data
        
        # Write updated subtitles back to SRT file
        subtitles_path = session.get('subtitles_path')
        if subtitles_path:
            dict_to_srt(subtitles_data, subtitles_path)
            return json.dumps({'success': True})
        else:
            return json.dumps({'success': False, 'error': 'Subtitles path not found'}), 400
    
    except Exception as e:
        app.logger.error(f"Error saving subtitles: {str(e)}")
        return json.dumps({'success': False, 'error': str(e)}), 500

@app.route('/detect_language', methods=['POST'])
def detect_subtitle_language_route():
    if 'session_id' not in session or 'subtitles' not in session:
        return json.dumps({'success': False, 'error': 'Session expired'}), 400
    
    try:
        subtitles = session.get('subtitles', [])
        language_code = detect_subtitle_language(subtitles)
        
        # Map common language codes to names
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'ja': 'Japanese',
            'zh-cn': 'Chinese (Simplified)',
            'ar': 'Arabic',
            'ru': 'Russian',
            'pt': 'Portuguese',
            'pt-br': 'Portuguese (Brazil)',
            'hi': 'Hindi',
            'ko': 'Korean'
        }
        
        language_name = language_names.get(language_code, language_code)
        
        return json.dumps({
            'success': True, 
            'language_code': language_code,
            'language_name': language_name
        })
    
    except Exception as e:
        app.logger.error(f"Error detecting language: {str(e)}")
        return json.dumps({'success': False, 'error': str(e)}), 500

@app.route('/translate_subtitles', methods=['POST'])
def translate_subtitles_route():
    if 'session_id' not in session or 'subtitles' not in session:
        return json.dumps({'success': False, 'error': 'Session expired'}), 400
    
    try:
        # Always translate to Brazilian Portuguese regardless of what was requested
        # This is a key requirement for this application
        target_language = 'pt-br'
        subtitles = session.get('subtitles', [])
        
        app.logger.info("Translating to Brazilian Portuguese (using 'pt-br' code, will be handled as 'pt' internally)")
        
        # Translate the subtitles - the translate_subtitles function will handle pt-br internally
        translated_subtitles = translate_subtitles(subtitles, target_language)
        
        # Update session and SRT file
        session['subtitles'] = translated_subtitles
        subtitles_path = session.get('subtitles_path')
        
        if subtitles_path:
            dict_to_srt(translated_subtitles, subtitles_path)
            
        return json.dumps({
            'success': True,
            'subtitles': translated_subtitles
        })
    
    except Exception as e:
        app.logger.error(f"Error translating subtitles: {str(e)}")
        return json.dumps({'success': False, 'error': str(e)}), 500

@app.route('/generate_video', methods=['POST'])
def generate_video():
    if 'session_id' not in session or 'video_path' not in session or 'subtitles_path' not in session:
        flash('Session data missing', 'danger')
        return redirect(url_for('index'))
    
    try:
        session_id = session['session_id']
        video_path = session['video_path']
        subtitles_path = session['subtitles_path']
        
        # Get subtitle styling options from form
        font_size = request.form.get('font_size', '24')
        font_color = request.form.get('font_color', 'white')
        bg_color = request.form.get('bg_color', 'black')
        position = request.form.get('position', 'bottom')
        subtitle_width = request.form.get('subtitle_width', '80')
        
        # Get custom position if specified
        custom_pos_x = request.form.get('custom_pos_x', '50')
        custom_pos_y = request.form.get('custom_pos_y', '90')
        
        # Handle custom positioning
        custom_position = False
        if position == 'custom' and custom_pos_x and custom_pos_y:
            try:
                # Convert to integers for validation
                pos_x = int(custom_pos_x)
                pos_y = int(custom_pos_y)
                
                # If valid, set custom_position to True
                if 0 <= pos_x <= 100 and 0 <= pos_y <= 100:
                    custom_position = True
                    app.logger.info(f"Using custom subtitle position: x={pos_x}%, y={pos_y}%")
            except ValueError:
                app.logger.warning("Invalid custom position values, falling back to default position")
        
        # Create output path
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        output_filename = f"subtitled_{os.path.basename(video_path)}"
        output_path = os.path.join(session_folder, output_filename)
        
        # Add custom position and width options to embed_subtitles call
        app.logger.info(f"Generating video with subtitles from {video_path} to {output_path}")
        app.logger.info(f"Subtitle styling: size={font_size}, color={font_color}, bg={bg_color}, position={position}")
        app.logger.info(f"Custom position: {custom_position}, x={custom_pos_x}, y={custom_pos_y}, width={subtitle_width}")
        
        try:
            embed_subtitles(
                video_path, 
                subtitles_path, 
                output_path, 
                font_size=int(font_size),
                font_color=font_color,
                bg_color=bg_color,
                position=position,
                custom_position=custom_position,
                custom_pos_x=int(custom_pos_x) if custom_position else 50,
                custom_pos_y=int(custom_pos_y) if custom_position else 90,
                subtitle_width=int(subtitle_width),
                font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            )
            app.logger.info(f"Successfully generated video with subtitles: {output_path}")
        except Exception as e:
            app.logger.error(f"Error in embed_subtitles: {str(e)}")
            app.logger.error(f"Video path exists: {os.path.exists(video_path)}")
            app.logger.error(f"Subtitles path exists: {os.path.exists(subtitles_path)}")
            app.logger.error(f"Output directory exists: {os.path.exists(os.path.dirname(output_path))}")
            raise
        
        session['output_path'] = output_path
        session['output_filename'] = output_filename
        
        # Redirect to the preview page instead of download page
        return redirect(url_for('preview_video'))
    
    except Exception as e:
        app.logger.error(f"Error generating video: {str(e)}")
        flash(f'Error generating video: {str(e)}', 'danger')
        return redirect(url_for('edit_subtitles'))

@app.route('/preview')
def preview_video():
    if 'output_filename' not in session:
        flash('No processed video found', 'warning')
        return redirect(url_for('index'))
    
    # Get the required information for the preview page
    output_filename = session.get('output_filename')
    session_id = session.get('session_id')
    
    return render_template('preview.html', 
                          filename=output_filename,
                          session_id=session_id)

@app.route('/download_page')
def download_page():
    if 'output_filename' not in session:
        flash('No processed video found', 'warning')
        return redirect(url_for('index'))
    
    output_filename = session['output_filename']
    return render_template('index.html', download_ready=True, filename=output_filename)

@app.route('/download/<filename>')
def download_file(filename):
    if 'session_id' not in session:
        flash('Session expired', 'danger')
        return redirect(url_for('index'))
    
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['session_id'])
    return send_from_directory(session_folder, filename, as_attachment=True)

@app.route('/video/<session_id>/<filename>')
def serve_video(session_id, filename):
    if 'session_id' not in session or session['session_id'] != session_id:
        return "Unauthorized", 403
    
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    return send_from_directory(session_folder, filename)

@app.route('/clear_session', methods=['POST'])
def clear_session():
    if 'session_id' in session:
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['session_id'])
        if os.path.exists(session_folder):
            try:
                shutil.rmtree(session_folder)
            except Exception as e:
                app.logger.error(f"Error removing session folder: {str(e)}")
    
    session.clear()
    flash('Session cleared', 'info')
    return redirect(url_for('index'))

# Clean up old session folders periodically (files older than 1 hour)
@app.before_request
def cleanup_old_sessions():
    try:
        current_time = time.time()
        for folder_name in os.listdir(UPLOAD_FOLDER):
            folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
            if os.path.isdir(folder_path):
                folder_modified_time = os.path.getmtime(folder_path)
                if current_time - folder_modified_time > 3600:  # 1 hour
                    shutil.rmtree(folder_path)
    except Exception as e:
        app.logger.error(f"Error during cleanup: {str(e)}")
