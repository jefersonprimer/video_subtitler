# Video Subtitling Web Application

## Project Description

This web application is designed to streamline the process of adding subtitles to videos. It leverages a robust set of tools and libraries to handle video and audio processing efficiently. The core functionality involves taking a user-uploaded video, extracting the audio from it, generating subtitles based on the spoken content, and then embedding these subtitles into a new video file.

Here's a detailed breakdown of the process:

1.  **Video Upload**: Users can upload video files of various formats through the application's web interface.
2.  **Audio Extraction**: Once a video is uploaded, the application extracts the audio track from it. This audio is temporarily stored and used for the next step.
3.  **Subtitle Generation**: The extracted audio is processed using advanced speech recognition technology (Whisper) to transcribe the spoken words into text. This transcription forms the basis of the subtitles. The application generates subtitles automatically using the speech recognition. The application generates the subtitles in english, and then it is translated to brazilian portuguese.
4.  **Subtitle Editing**: Before the subtitles are embedded, users are given the opportunity to review and edit the automatically generated subtitles. This allows for corrections in case the speech recognition made any mistakes.
5.  **Subtitle Customization**: Users can customize the appearance of the subtitles to match their preferences or the style of the video. This includes:
    *   **Font Size**: Adjusting the size of the text to ensure readability.
    *   **Color**: Changing the color of the subtitle text.
    *   **Background**: Adding a background behind the subtitles to make them stand out against the video content.
    *   **Position**: Altering the vertical position of the subtitles on the screen.
    *   **Subtitle Width:** Adjusting the width of the subtitle text box.
6.  **Subtitle Embedding**: Once the subtitles are finalized, they are embedded into the original video file. This process ensures that the subtitles are synchronized with the video's audio.
7.  **Download**: Finally, the user can download the new video file, which now contains the embedded subtitles.

## Dependencies

The application requires the following Python libraries:

*   `decorator>=5.2.1`
*   `deep-translator>=1.11.4`
*   `email-validator>=2.2.0`
*   `faster-whisper>=1.1.1`
*   `ffmpeg-python>=0.2.0`
*   `flask>=3.1.0`
*   `flask-sqlalchemy>=3.1.1`
*   `gunicorn>=23.0.0`
*   `imageio>=2.37.0`
*   `imageio-ffmpeg>=0.6.0`
*   `langdetect>=1.0.9`
*   `moviepy>=2.1.2`
*   `numpy>=2.2.4`
*   `openai>=1.71.0`
*   `proglog>=0.1.11`
*   `psycopg2-binary>=2.9.10`
*   `pydub>=0.25.1`
*   `python-ffmpeg>=2.0.12`
*   `speechrecognition>=3.14.2`
*   `tqdm>=4.67.1`
*   `werkzeug>=3.1.3`
*   `whisper>=1.1.10`

## Installation

1.  **Clone the Repository:**
```
bash
    git clone <repository-url>
    cd <repository-directory>
    
```
2.  **Create a Virtual Environment (Recommended):**
```
bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    
```
3.  **Install Dependencies:**
```
bash
    pip install -r requirements.txt
    
```
Or if you do not have a requirements.txt file, you can install the dependencies directly from the pyproject.toml:
```
bash
    pip install decorator deep-translator email-validator faster-whisper ffmpeg-python flask flask-sqlalchemy gunicorn imageio imageio-ffmpeg langdetect moviepy numpy openai proglog psycopg2-binary pydub python-ffmpeg speechrecognition tqdm werkzeug whisper
        
```
4.  **Environment Configuration:**
    *   Ensure that FFmpeg is installed on your system, as it is required for video processing. You can install it using your system's package manager (e.g., `apt-get install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS).

## Running the Application

To run the application, use `gunicorn` as follows:
```
bash
gunicorn app:app
```
This command starts the application using Gunicorn, serving the Flask app defined in `app.py`.

## Usage

1.  **Upload a Video:** Navigate to the web application in your browser (usually `http://127.0.0.1:8000` if running locally). Use the upload form to select and upload your video file.
2.  **Generate Subtitles:** Once the video is uploaded, the application will automatically extract the audio and generate subtitles in english, then translated to brazilian portuguese.
3.  **Edit Subtitles:** Review the generated subtitles and make any necessary corrections via the provided text editor.
4.  **Customize Subtitles:** Customize the appearance of the subtitles using the available options:
    *   **Font Size:** Select the desired text size.
    *   **Color:** Choose the text color.
    *   **Background:** Add or remove a background behind the subtitles.
    *   **Position:** Adjust the subtitle position on the screen.
    * **Subtitle Width:** Set the width of the subtitle text box.
5.  **Download Subtitled Video:** Once you are satisfied with the subtitles and their appearance, click the download button to get the new subtitled video file.

## Error Handling

The application includes error handling to manage common issues:

*   **Incorrect File Types:** If a user uploads a file that is not a supported video format, the application will display an error message, preventing the upload.
*   **Missing Video Files:** If a video file cannot be found or accessed, the application will notify the user with an appropriate error message.
* **Errors in Subtitle Generation:** If a error happens when generating subtitles, a error will be displayed.

## Additional Notes

*   **Temporary Files:** The application uses temporary folders to store the extracted audio and intermediate video files. These files are automatically deleted after 1 hour to conserve disk space.
* **Audio files:** The audio files are extracted from the video and are also stored temporarily.
* **Brazilian Portuguese:** The subtitles are automatically translated to brazilian portuguese.