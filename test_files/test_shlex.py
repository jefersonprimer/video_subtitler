import subprocess
import shlex
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

subtitles_path = "test.srt"
video_path = "test_pt_with_audio.mp4"
output_path = "test_shlex_quote.mp4"

style_opts = (
    f"FontSize=24,"
    f"Alignment=2,"
    f"MarginV=35,"
    f"MarginL=10,"
    f"MarginR=10,"
    f"BorderStyle=4,"
    f"LineSpacing=0,"
    f"Bold=1,"
    f"WrapStyle=0,"
    f"MaxLines=1"
)

command = [
    'ffmpeg',
    '-i', video_path,
    '-vf', f"subtitles={shlex.quote(subtitles_path)}:force_style='{style_opts}'",
    '-c:v', 'libx264',
    '-c:a', 'aac',
    '-preset', 'medium',
    '-movflags', '+faststart',
    output_path
]

cmd_str = ' '.join(command)
logger.info(f"Running command: {cmd_str}")

try:
    result = subprocess.run(command, check=True, capture_output=True)
    logger.info("Command succeeded")
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e.stderr.decode() if e.stderr else 'No error output'}")
    logger.error(f"Return code: {e.returncode}")
