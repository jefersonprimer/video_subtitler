import os
import subprocess
import json
import logging
import shlex

logger = logging.getLogger(__name__)

def extract_audio(video_path, output_audio_path):
    """
    Extract audio from a video file using FFmpeg
    
    Args:
        video_path (str): Path to the input video file
        output_audio_path (str): Path where the extracted audio will be saved
    """
    try:
        command = [
            'ffmpeg', '-i', video_path, 
            '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1',
            output_audio_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        logger.info(f"Successfully extracted audio to {output_audio_path}")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        raise RuntimeError(f"Failed to extract audio: {e.stderr.decode()}")
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def get_video_info(video_path):
    """
    Get information about a video file using FFprobe
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Information about the video file
    """
    try:
        command = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        video_info = json.loads(result.stdout)
        
        # Extract relevant information
        info = {
            'format': video_info.get('format', {}).get('format_name', 'unknown'),
            'duration': float(video_info.get('format', {}).get('duration', 0)),
            'size': int(video_info.get('format', {}).get('size', 0))
        }
        
        # Get video stream information
        for stream in video_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                info['width'] = stream.get('width', 0)
                info['height'] = stream.get('height', 0)
                info['codec'] = stream.get('codec_name', 'unknown')
                break
        
        return info
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        raise RuntimeError(f"Failed to get video info: {e.stderr}")
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise

def embed_subtitles(video_path, subtitles_path, output_path, 
                    font_size=24, font_color='white', bg_color='black', position='bottom', 
                    custom_position=False, custom_pos_x=50, custom_pos_y=90, subtitle_width=80,
                    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
    """
    Embed subtitles into a video using FFmpeg directly
    
    Args:
        video_path (str): Path to the input video file
        subtitles_path (str): Path to the SRT subtitles file
        output_path (str): Path where the output video will be saved
        font_size (int): Font size for subtitles
        font_color (str): Font color for subtitles
        bg_color (str): Background color for subtitles
        position (str): Position of subtitles ('bottom', 'top', 'center')
        font (str): Path to font file for subtitles
    """
    try:
        # Determine vertical position (default to bottom)
        vertical_position = position.lower()
        if vertical_position not in ['bottom', 'top', 'center', 'custom']:
            vertical_position = 'bottom'
            
        # Subtitle width adjustment (calculate MarginL and MarginR)
        # For a width of 80%, we would have 10% margin on each side (for center alignment)
        margin_percent = int((100 - subtitle_width) / 2)
        margin_l = margin_percent
        margin_r = margin_percent
            
        # Handle custom positioning
        if custom_position and vertical_position == 'custom':
            logger.info(f"Using custom subtitle position: x={custom_pos_x}%, y={custom_pos_y}%")
            # Calculate alignment based on custom position
            # We'll use 2 (bottom center) as default
            alignment = '2'
            
            # Update the position and alignment based on the custom position
            if custom_pos_y < 33:  # Top third of the screen
                alignment = '6'  # Top center
            elif custom_pos_y < 66:  # Middle third
                alignment = '10'  # Middle center
            else:  # Bottom third
                alignment = '2'  # Bottom center
        else:
            # Default positions
            # Convert position to ffmpeg subtitle style parameters
            position_map = {
                'bottom': '(main_w-text_w)/2:main_h-(text_h*2)',
                'top': '(main_w-text_w)/2:text_h',
                'center': '(main_w-text_w)/2:(main_h-text_h)/2'
            }
            
            # Determine the alignment value based on position
            alignment_map = {
                'bottom': '2',  # Bottom center
                'top': '6',     # Top center
                'center': '10'  # Middle center
            }
            alignment = alignment_map.get(position, '2')
        
        # Create ffmpeg command with proper escaping of the subtitle path
        escaped_subtitles_path = subtitles_path.replace("'", "'\\''")
        
        
        # Additional style options to enforce single-line subtitles
        # BorderStyle=4 adds an opaque box background, 1 for outline only (transparent bg)
        # MarginV adds vertical margin to prevent overlap
        # LineSpacing=0 ensures no additional line spacing
        # Bold=1 makes text bold for better readability
        # WrapStyle=0 forces one line per subtitle (crucial)
        # PrimaryColour sets text color - uses FFmpeg ASS format (ABGR)
        # BackColour sets background color - uses FFmpeg ASS format (ABGR)
        
        # Handle transparent background
        if bg_color.lower() == 'transparent':
            border_style = "1"  # Outline only
            outline_color = "&H000000&"  # Black outline for better visibility
            outline_size = "2"  # Thicker outline for better visibility with transparent bg
        else:
            border_style = "4"  # Opaque box
            outline_color = "&H000000&"  # Default black outline
            outline_size = "1"  # Standard outline size
        
        # Map common color names to ASS hex format (ABGR)
        color_map = {
            'white': '&HFFFFFF&',
            'black': '&H000000&',
            'yellow': '&H00FFFF&',  # ABGR format
            'lime': '&H00FF00&',
            'cyan': '&HFFFF00&',
            'magenta': '&HFF00FF&',
            'red': '&H0000FF&',
            'orange': '&H0080FF&',
            'aliceblue': '&HFFF8F0&',
            'pink': '&HC0C0FF&',
            'navy': '&H800000&',
            'darkred': '&H000080&',
            'darkgreen': '&H008000&',
            'purple': '&H800080&',
            'gray': '&H808080&',
            'brown': '&H2A2AA5&',
            'transparent': '&H00FFFFFF&'  # Fully transparent
        }
        
        # Get color codes or use defaults
        primary_color = color_map.get(font_color.lower(), '&HFFFFFF&')  # Default white
        back_color = color_map.get(bg_color.lower(), '&H000000&')  # Default black
        
        logger.info(f"Using font color: {font_color} ({primary_color}), bg color: {bg_color} ({back_color})")
        logger.info(f"Font size setting: {font_size}px")
        
        # Implementation for actually using correct font size
        # For some reason, the ASS subtitle format in FFmpeg needs special handling for small font sizes
        # The strategy: we use the requested font size and adjust everything else to make it work
        
        # For small sizes (16-20px), we need to increase the base resolution while keeping the font size
        if int(font_size) <= 20:
            # Use higher resolution with same font size for small font settings
            play_res_x = 1920  # Higher resolution
            play_res_y = 1080  # Higher resolution
            shadow_size = 0    # Disable shadow for small fonts
            outline_size = 1   # Minimal outline for small fonts
            font_scale = 1.0   # Normal scale
        else:
            # For larger fonts, use standard resolution
            play_res_x = 1280
            play_res_y = 720
            shadow_size = 0    # Disable shadow
            outline_size = outline_size  # Use calculated outline size
            font_scale = 1.0   # Normal scale
            
        logger.info(f"Using font size: {font_size}px with resolution {play_res_x}x{play_res_y}")
            
        style_opts = (
            f"FontName=DejaVuSans,"
            f"FontSize={font_size},"
            f"PlayResX={play_res_x},"
            f"PlayResY={play_res_y},"
            f"ScaledBorderAndShadow=yes,"
            f"Shadow={shadow_size},"
            f"Alignment={alignment},"
            f"MarginV=35,"
            f"MarginL={margin_l},"
            f"MarginR={margin_r},"
            f"BorderStyle={border_style},"
            f"OutlineColour={outline_color},"
            f"Outline={outline_size},"
            f"PrimaryColour={primary_color},"
            f"BackColour={back_color},"
            f"LineSpacing=0,"
            f"Bold=1,"
            f"WrapStyle=0,"
            f"MaxLines=1"
        )
        
        # Modified approach without using fontsizes parameter since it's not supported
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles={subtitles_path}:force_style='{style_opts}'",
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'medium',
            '-movflags', '+faststart',
            output_path
        ]
        
        # Run FFmpeg
        cmd_str = ' '.join(command)
        logger.info(f"Running FFmpeg command to embed subtitles: {cmd_str}")
        try:
            result = subprocess.run(command, check=True, capture_output=True)
            logger.info(f"Successfully embedded subtitles in {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg command failed: {cmd_str}")
            logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")
            logger.error(f"Return code: {e.returncode}")
            raise
    
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        
        # Fall back to a simpler approach with modified subtitle file
        try:
            logger.info("Falling back to alternative subtitle embedding approach")
            
            # Create a temporary ASS subtitle file with specific styling to ensure single line
            temp_ass_path = subtitles_path + '.ass'
            
            # Get the position type again for the fallback method
            fallback_vertical_position = position.lower()
            if fallback_vertical_position not in ['bottom', 'top', 'center', 'custom']:
                fallback_vertical_position = 'bottom'
                
            # Handle custom positioning for fallback method
            if custom_position and fallback_vertical_position == 'custom':
                # Calculate fallback alignment based on custom position
                if custom_pos_y < 33:  # Top third of the screen
                    fallback_alignment = '6'  # Top center
                elif custom_pos_y < 66:  # Middle third
                    fallback_alignment = '10'  # Middle center
                else:  # Bottom third
                    fallback_alignment = '2'  # Bottom center
            else:
                # Define alignment map for the fallback approach
                fallback_alignment_map = {
                    'bottom': '2',  # Bottom center
                    'top': '6',     # Top center
                    'center': '10'  # Middle center
                }
                
                # Use the position to determine the alignment value
                fallback_alignment = fallback_alignment_map.get(position, '2')
            
            # Calculate margin percentages for fallback method
            # Recalculate to avoid using potentially unbound variables
            fallback_margin_percent = int((100 - subtitle_width) / 2)
            fallback_margin_l = fallback_margin_percent
            fallback_margin_r = fallback_margin_percent
            
            # Reuse the same color handling from the main method
            # Handle transparent background for fallback method
            if bg_color.lower() == 'transparent':
                fallback_border_style = "1"  # Outline only
                fallback_outline_color = "&H000000&"  # Black outline
                fallback_outline_size = "2"  # Thicker outline
            else:
                fallback_border_style = "4"  # Opaque box
                fallback_outline_color = "&H000000&"  # Black outline
                fallback_outline_size = "1"  # Standard outline
               
            # Define fallback color map (same as the one above)
            fallback_color_map = {
                'white': '&HFFFFFF&',
                'black': '&H000000&',
                'yellow': '&H00FFFF&',  # ABGR format
                'lime': '&H00FF00&',
                'cyan': '&HFFFF00&',
                'magenta': '&HFF00FF&',
                'red': '&H0000FF&',
                'orange': '&H0080FF&',
                'aliceblue': '&HFFF8F0&',
                'pink': '&HC0C0FF&',
                'navy': '&H800000&',
                'darkred': '&H000080&',
                'darkgreen': '&H008000&',
                'purple': '&H800080&',
                'gray': '&H808080&',
                'brown': '&H2A2AA5&',
                'transparent': '&H00FFFFFF&'  # Fully transparent
            }
                
            # Use our fallback color map
            fallback_primary_color = fallback_color_map.get(font_color.lower(), '&HFFFFFF&')  # Default white
            fallback_back_color = fallback_color_map.get(bg_color.lower(), '&H000000&')  # Default black
            
            logger.info(f"Fallback using font color: {font_color} ({fallback_primary_color}), bg color: {bg_color} ({fallback_back_color})")
            
            # Convert SRT to ASS with custom style
            style_options = (
                f"Style='FontSize={font_size},"
                f"Bold=1,"
                f"Alignment={fallback_alignment},"
                f"MarginL={fallback_margin_l},"
                f"MarginR={fallback_margin_r},"
                f"BorderStyle={fallback_border_style},"
                f"OutlineColour={fallback_outline_color},"
                f"Outline={fallback_outline_size},"
                f"PrimaryColour={fallback_primary_color},"
                f"BackColour={fallback_back_color},"
                f"WrapStyle=0,"
                f"MaxLines=1'"
            )
            
            convert_cmd = [
                'ffmpeg',
                '-i', subtitles_path,
                '-c:s', 'ass',
                '-map_metadata', '-1',
                '-metadata:s:s:0', style_options,
                temp_ass_path
            ]
            
            # Log the conversion command
            convert_cmd_str = ' '.join(convert_cmd)
            logger.info(f"Converting SRT to ASS with command: {convert_cmd_str}")
            
            try:
                result = subprocess.run(convert_cmd, check=True, capture_output=True)
                logger.info(f"Converted SRT to ASS format: {temp_ass_path}")
                
                # Use the ASS file with specific style settings
                # Add custom ASS style filter to ensure single line display
                logger.info(f"Fallback style using font size: {font_size}px")
                
                # Similar font size adjustment for fallback method
                # For small sizes, we use higher resolution
                if int(font_size) <= 20:
                    fallback_play_res_x = 1920  # Higher resolution
                    fallback_play_res_y = 1080  # Higher resolution
                    fallback_shadow_size = 0    # No shadow
                    fallback_font_size = font_size
                else:
                    fallback_play_res_x = 1280  # Standard resolution
                    fallback_play_res_y = 720   # Standard resolution
                    fallback_shadow_size = 0    # No shadow
                    fallback_font_size = font_size
                    
                logger.info(f"Fallback font size: {fallback_font_size}px with resolution {fallback_play_res_x}x{fallback_play_res_y}")
                
                custom_ass_style = (
                    f"FontName=DejaVuSans,"  # Explicit font name
                    f"FontSize={fallback_font_size},"  # Font size
                    f"PlayResX={fallback_play_res_x},"  # Resolution width
                    f"PlayResY={fallback_play_res_y},"  # Resolution height
                    f"ScaledBorderAndShadow=yes,"  # Scale borders with font
                    f"Shadow={fallback_shadow_size},"  # Shadow size
                    f"Alignment={fallback_alignment},"
                    f"MarginV=35,"
                    f"MarginL={fallback_margin_l},"
                    f"MarginR={fallback_margin_r},"
                    f"BorderStyle={fallback_border_style},"
                    f"OutlineColour={fallback_outline_color},"
                    f"Outline={fallback_outline_size},"
                    f"PrimaryColour={fallback_primary_color},"
                    f"BackColour={fallback_back_color},"
                    f"LineSpacing=0,"
                    f"Bold=1,"
                    f"WrapStyle=0,"
                    f"MaxLines=1"
                )
                
                # Modified fallback approach without using fontsizes parameter
                command = [
                    'ffmpeg',
                    '-i', video_path,
                    '-vf', f"ass={temp_ass_path}:fontsdir=/usr/share/fonts/truetype/dejavu:force_style='{custom_ass_style}'",
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'medium',
                    '-movflags', '+faststart',
                    output_path
                ]
                
                fallback_cmd_str = ' '.join(command)
                logger.info(f"Embedding subtitles with fallback method: {fallback_cmd_str}")
                
                result2 = subprocess.run(command, check=True, capture_output=True)
                logger.info(f"Successfully embedded subtitles using fallback method in {output_path}")
                return True
            except subprocess.CalledProcessError as conv_err:
                logger.error(f"SRT to ASS conversion failed: {conv_err.stderr.decode() if conv_err.stderr else 'No error output'}")
                logger.error(f"Return code: {conv_err.returncode}")
                raise
            
        except subprocess.CalledProcessError as e2:
            logger.error(f"FFmpeg fallback error: {e2.stderr.decode() if e2.stderr else 'Unknown error'}")
            raise RuntimeError(f"Failed to embed subtitles: {e.stderr.decode() if e.stderr else 'Unknown error'}")
    
    except Exception as e:
        logger.error(f"Error embedding subtitles: {str(e)}")
        raise

def parse_time_code(time_code):
    """
    Parse SRT time code to seconds
    
    Args:
        time_code (str): Time code in format HH:MM:SS,mmm
        
    Returns:
        float: Time in seconds
    """
    parts = time_code.replace(',', ':').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = int(parts[3])
    
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
