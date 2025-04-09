import os
import logging
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tempfile
import langdetect
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel
import speech_recognition as sr

logger = logging.getLogger(__name__)

def generate_subtitles(audio_path, output_srt_path, min_silence_len=500, silence_thresh=-40, keep_silence=300, use_whisper=True, whisper_model="base"):
    """
    Generate SRT subtitles from an audio file
    
    Args:
        audio_path (str): Path to the audio file
        output_srt_path (str): Path where the SRT file will be saved
        min_silence_len (int): Minimum length of silence (in ms) to split on
        silence_thresh (int): Silence threshold (in dB)
        keep_silence (int): Amount of silence to keep (in ms)
        use_whisper (bool): Whether to use Whisper for transcription (preferred for accuracy)
        whisper_model (str): Whisper model to use ("tiny", "base", "small", "medium")
    """
    try:
        logger.info(f"Generating subtitles for {audio_path}")
        
        if use_whisper:
            return generate_whisper_subtitles(audio_path, output_srt_path, model_name=whisper_model)
        else:
            return generate_google_subtitles(audio_path, output_srt_path, min_silence_len, silence_thresh, keep_silence)
    
    except Exception as e:
        logger.error(f"Error generating subtitles: {str(e)}")
        raise

def generate_whisper_subtitles(audio_path, output_srt_path, model_name="base"):
    """
    Generate subtitles using Whisper model locally
    
    Args:
        audio_path (str): Path to the audio file
        output_srt_path (str): Path where the SRT file will be saved
        model_name (str): Whisper model to use ("tiny", "base", "small", "medium")
    """
    try:
        logger.info(f"Loading Whisper model: {model_name}")
        # Load the Whisper model
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        
        logger.info("Transcribing audio with Whisper...")
        # Transcribe audio
        segments, info = model.transcribe(audio_path, beam_size=5, language=None)
        
        logger.info(f"Detected language: {info.language} with probability {info.language_probability:.2f}")
        
        # Process segments and generate subtitles
        subtitles = []
        
        subtitle_index = 1
        for segment in segments:
            # Extract timing information
            start_time = segment.start
            end_time = segment.end
            text = segment.text.strip()
            
            if text:
                # Remove any existing line breaks
                text = text.replace('\n', ' ').replace('\r', '')
                
                # Check if the text is too long (more than 35 characters)
                # If so, split it into multiple subtitles
                max_chars = 35
                
                if len(text) <= max_chars:
                    # Short enough for a single subtitle
                    subtitles.append({
                        "index": subtitle_index,
                        "start": format_time(start_time),
                        "end": format_time(end_time),
                        "text": text
                    })
                    subtitle_index += 1
                else:
                    # Split into multiple subtitles
                    words = text.split()
                    current_line = ""
                    lines = []
                    
                    # Group words into lines with max_chars limit
                    for word in words:
                        if len(current_line + " " + word) <= max_chars or current_line == "":
                            if current_line:
                                current_line += " " + word
                            else:
                                current_line = word
                        else:
                            lines.append(current_line)
                            current_line = word
                    
                    # Add the last line if it's not empty
                    if current_line:
                        lines.append(current_line)
                    
                    # Calculate time for each split subtitle
                    duration = end_time - start_time
                    time_per_line = duration / len(lines)
                    
                    # Create a subtitle entry for each line
                    for i, line in enumerate(lines):
                        line_start = start_time + (i * time_per_line)
                        line_end = line_start + time_per_line
                        
                        subtitles.append({
                            "index": subtitle_index,
                            "start": format_time(line_start),
                            "end": format_time(line_end),
                            "text": line
                        })
                        subtitle_index += 1
        
        # Write SRT file
        write_srt(subtitles, output_srt_path)
        logger.info(f"Generated {len(subtitles)} subtitles using Whisper, saved to {output_srt_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating Whisper subtitles: {str(e)}")
        logger.warning("Falling back to Google Speech Recognition")
        return generate_google_subtitles(audio_path, output_srt_path)

def generate_google_subtitles(audio_path, output_srt_path, min_silence_len=500, silence_thresh=-40, keep_silence=300):
    """
    Generate subtitles using Google Speech Recognition
    
    Args:
        audio_path (str): Path to the audio file
        output_srt_path (str): Path where the SRT file will be saved
        min_silence_len (int): Minimum length of silence (in ms) to split on
        silence_thresh (int): Silence threshold (in dB)
        keep_silence (int): Amount of silence to keep (in ms)
    """
    try:
        # Split audio on silence
        audio = AudioSegment.from_file(audio_path)
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=keep_silence
        )
        
        logger.info(f"Split audio into {len(chunks)} chunks")
        
        # Initialize speech recognizer
        recognizer = sr.Recognizer()
        
        # Process chunks and generate subtitles
        subtitles = []
        current_time = 0
        
        # Create a temporary directory for audio chunks
        temp_dir = os.path.dirname(audio_path)
        
        for i, chunk in enumerate(chunks):
            # Calculate timing
            start_time = current_time
            chunk_duration = len(chunk) / 1000.0  # Convert to seconds
            end_time = start_time + chunk_duration
            
            # Save chunk to temporary file
            chunk_path = os.path.join(temp_dir, f"chunk_{i}.wav")
            chunk.export(chunk_path, format="wav")
            
            # Recognize speech in chunk
            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    if text:
                        # Remove any line breaks
                        text = text.replace('\n', ' ').replace('\r', '')
                        
                        # Check if the text is too long (more than 35 characters to ensure single line)
                        max_chars = 35
                        
                        if len(text) <= max_chars:
                            # Short enough for a single subtitle
                            subtitles.append({
                                "index": len(subtitles) + 1,
                                "start": format_time(start_time),
                                "end": format_time(end_time),
                                "text": text
                            })
                        else:
                            # Split into multiple subtitles
                            words = text.split()
                            current_line = ""
                            lines = []
                            
                            # Group words into lines with max_chars limit
                            for word in words:
                                if len(current_line + " " + word) <= max_chars or current_line == "":
                                    if current_line:
                                        current_line += " " + word
                                    else:
                                        current_line = word
                                else:
                                    lines.append(current_line)
                                    current_line = word
                            
                            # Add the last line if it's not empty
                            if current_line:
                                lines.append(current_line)
                            
                            # Calculate time for each split subtitle
                            duration = end_time - start_time
                            time_per_line = duration / len(lines)
                            
                            # Create a subtitle entry for each line
                            for j, line in enumerate(lines):
                                line_start = start_time + (j * time_per_line)
                                line_end = line_start + time_per_line
                                
                                subtitles.append({
                                    "index": len(subtitles) + 1,
                                    "start": format_time(line_start),
                                    "end": format_time(line_end),
                                    "text": line
                                })
                        logger.debug(f"Recognized: {text}")
                except sr.UnknownValueError:
                    logger.debug(f"Speech recognition could not understand audio chunk {i}")
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service: {e}")
                
            # Clean up temporary file
            try:
                os.remove(chunk_path)
            except:
                pass
            
            # Update current time
            current_time = end_time
        
        # Write SRT file
        write_srt(subtitles, output_srt_path)
        logger.info(f"Generated subtitles saved to {output_srt_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error generating Google subtitles: {str(e)}")
        raise

def write_srt(subtitles, output_path):
    """
    Write subtitles to SRT file
    
    Args:
        subtitles (list): List of subtitle dictionaries
        output_path (str): Path where to save the SRT file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, subtitle in enumerate(subtitles):
            f.write(f"{subtitle['index']}\n")
            f.write(f"{subtitle['start']} --> {subtitle['end']}\n")
            f.write(f"{subtitle['text']}\n\n")

def format_time(seconds):
    """
    Format time in SRT format (HH:MM:SS,mmm)
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def srt_to_dict(srt_path):
    """
    Parse SRT file to a list of dictionaries
    
    Args:
        srt_path (str): Path to the SRT file
        
    Returns:
        list: List of subtitle dictionaries
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        blocks = content.split('\n\n')
        subtitles = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # Get index
                index = int(lines[0])
                
                # Parse time codes
                time_codes = lines[1].split(' --> ')
                start_time = time_codes[0]
                end_time = time_codes[1]
                
                # Join the text lines and remove any line breaks
                text = ' '.join(lines[2:]).replace('\n', ' ').replace('\r', '')
                
                # Check if the text is too long (more than 35 characters to ensure single line)
                max_chars = 35
                
                if len(text) <= max_chars:
                    # Short enough for a single subtitle
                    subtitles.append({
                        "index": index,
                        "start": start_time,
                        "end": end_time,
                        "text": text
                    })
                else:
                    # If the text is too long, split it into multiple subtitles with reindexing
                    words = text.split()
                    current_line = ""
                    split_lines = []
                    
                    # Group words into lines with max_chars limit
                    for word in words:
                        if len(current_line + " " + word) <= max_chars or current_line == "":
                            if current_line:
                                current_line += " " + word
                            else:
                                current_line = word
                        else:
                            split_lines.append(current_line)
                            current_line = word
                    
                    # Add the last line if it's not empty
                    if current_line:
                        split_lines.append(current_line)
                    
                    # Add the divided subtitles
                    for line in split_lines:
                        subtitles.append({
                            "index": len(subtitles) + 1,
                            "start": start_time,
                            "end": end_time,
                            "text": line
                        })
        
        return subtitles
    
    except Exception as e:
        logger.error(f"Error parsing SRT file: {str(e)}")
        return []

def dict_to_srt(subtitles, output_path):
    """
    Convert list of subtitle dictionaries to SRT file
    
    Args:
        subtitles (list): List of subtitle dictionaries
        output_path (str): Path where to save the SRT file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for subtitle in subtitles:
                # Ensure index is an integer
                index = subtitle['index']
                if isinstance(index, str):
                    try:
                        index = int(index)
                    except:
                        # Use position in list if conversion fails
                        pass
                
                # Write index
                f.write(f"{index}\n")
                
                # Write timing information
                f.write(f"{subtitle['start']} --> {subtitle['end']}\n")
                
                # Ensure the text has no line breaks and is properly formatted
                text = subtitle.get('text', '').replace('\n', ' ').replace('\r', '')
                
                # Write text
                f.write(f"{text}\n\n")
    
    except Exception as e:
        logger.error(f"Error writing SRT file: {str(e)}")
        raise

def detect_language(text):
    """
    Detect the language of the text
    
    Args:
        text (str): Text to detect language for
        
    Returns:
        str: ISO language code (e.g., 'en', 'fr', 'es', etc.)
    """
    try:
        # Combine all text to get better language detection
        return langdetect.detect(text)
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        return 'en'  # Default to English if detection fails

def detect_subtitle_language(subtitles):
    """
    Detect the language of subtitles
    
    Args:
        subtitles (list): List of subtitle dictionaries
        
    Returns:
        str: ISO language code (e.g., 'en', 'fr', 'es', etc.)
    """
    # Combine all subtitle text for better language detection
    all_text = ' '.join([s['text'] for s in subtitles if 'text' in s])
    if not all_text:
        return 'en'  # Default to English if no text
    
    return detect_language(all_text)

def translate_subtitles(subtitles, target_language='en'):
    """
    Translate subtitles to the target language
    
    Args:
        subtitles (list): List of subtitle dictionaries
        target_language (str): Target language code (e.g., 'en', 'fr', 'es', etc.)
        
    Returns:
        list: Translated subtitle dictionaries
    """
    if not subtitles:
        return []
    
    # Handle special case for Brazilian Portuguese
    if target_language == 'pt-br':
        target_language = 'pt'  # Use standard Portuguese for translation
    
    # Detect source language from the subtitles
    source_language = detect_subtitle_language(subtitles)
    
    # If source language is already Portuguese or Brazilian Portuguese and target is Portuguese or Brazilian Portuguese
    if (source_language in ['pt', 'pt-br']) and (target_language in ['pt', 'pt-br']):
        logger.info(f"Source language already matches target language (Portuguese), skipping translation")
        return subtitles
    
    logger.info(f"Translating subtitles from {source_language} to {target_language}")
    
    # Initialize the translator
    try:
        # Fix source language if needed
        if source_language == 'pt-br':
            source_language = 'pt'
            
        translator = GoogleTranslator(source=source_language, target=target_language)
        
        # Translate each subtitle
        translated_subtitles = []
        
        for subtitle in subtitles:
            # Create a copy of the subtitle
            translated_subtitle = subtitle.copy()
            
            # Translate the text
            if subtitle.get('text'):
                # Split text into smaller chunks if too long (to avoid API limits)
                text = subtitle['text']
                translated_text = ""
                
                # Remove any existing line breaks
                text = text.replace('\n', ' ').replace('\r', '')
                
                # Translate text
                translated_text = translator.translate(text)
                
                # Ensure translated text has no line breaks
                translated_text = translated_text.replace('\n', ' ').replace('\r', '')
                
                # Check if translated text is too long for a single line (more than 35 characters)
                max_chars = 35
                
                if len(translated_text) <= max_chars:
                    # Short enough for a single subtitle
                    translated_subtitle['text'] = translated_text
                else:
                    # If it's too long, we'll create multiple subtitle entries for this text
                    # First add this one with the original timing
                    translated_subtitle['text'] = translated_text
                    
                    # Add a note for debug that this subtitle may need splitting
                    logger.info(f"Translated text is longer than {max_chars} characters: {translated_text}")
                    
                    # Later, the subtitle will be split when it's written to the SRT file
            
            translated_subtitles.append(translated_subtitle)
        
        logger.info(f"Successfully translated {len(translated_subtitles)} subtitles")
        return translated_subtitles
    
    except Exception as e:
        logger.error(f"Error translating subtitles: {str(e)}")
        # Return original subtitles if translation fails
        return subtitles
