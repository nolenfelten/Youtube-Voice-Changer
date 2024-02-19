# Youtube-Voice-Changer
Use MetaVoice TTS to change a youtubers voice. 


## Step 1: Download Video and Closed Captions
yt-dlp

## Step 2: Process Captions and Segment Video
ffmpeg to mute video while saving parts of the video that the transcript dictates the size of to fit under MetaVoices character limit (220). The parts are named from the string of the transcript.

## Step 3: Generate Audio from Text
Use /tts endpoint to get audio file url that we download.

'''
from gradio_client import Client

client = Client("https://ttsdemo.themetavoice.xyz/")
result = client.predict(
		"Hello!!",	# str  in 'What should I say!? (max 220 characters).' Textbox component
		0,	# float (numeric value between 0.0 and 10.0) in 'Speech Stability - improves text following for a challenging speaker' Slider component
		1,	# float (numeric value between 1.0 and 5.0) in 'Speaker similarity - How closely to match speaker identity and speech style.' Slider component
		Preset voices,	# Literal[Preset voices, Upload target voice (atleast 30s)]  in 'Choose voice' Radio component
		Bria,	# Literal[Bria, Alex, Jacob]  in 'Preset voices' Dropdown component
		https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav,	# filepath  in 'Upload a clean sample to clone. Sample should contain 1 speaker, be between 30-90 seconds and not contain background noise.' Audio component
							api_name="/tts"
)
print(result)
'''


## Step 4: Merge Audio with Video Segments
FFMPEG conates with new audio.


