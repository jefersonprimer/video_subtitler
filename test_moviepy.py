import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

def test_subtitles():
    # Create a simple test text clip
    try:
        # Try creating a text clip with the new API
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        txt = TextClip(font=font_path, text="Test Subtitle", font_size=24, 
                      color='white', bg_color='black', method='caption',
                      size=(640, None))
        
        # Print available methods
        print("Available methods on TextClip:")
        methods = [method for method in dir(txt) if not method.startswith('_')]
        for method in sorted(methods):
            print(f"- {method}")
            
        # Test the with_position method
        positioned_clip = txt.with_position(('center', 100))
        print("\nSuccessfully positioned the clip")
        
        # Test the timing methods
        timed_clip = positioned_clip.with_start(0).with_end(5)
        print("Successfully set timing for the clip")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"Error in test: {str(e)}")

if __name__ == "__main__":
    test_subtitles()