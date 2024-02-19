# Youtube-Voice-Changer
Use MetaVoice TTS to change a youtubers voice. 


## Step 1: Download Video and Closed Captions
yt-dlp

```Python
import subprocess
import sys

def download_video_and_captions(url):
    try:
        subprocess.run(["yt-dlp", "-o", "video.mp4", "--write-auto-sub", "--sub-format", "srt", "--sub-lang", "en", url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download video and captions: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download YouTube video and captions.")
    parser.add_argument("-u", "--url", help="URL of the YouTube video to download", required=True)
    args = parser.parse_args()

    download_video_and_captions(args.url)
```

## Step 2: Process Captions and Segment Video
ffmpeg to mute video while saving parts of the video that the transcript dictates the size of to fit under MetaVoices character limit (220). The parts are named from the string of the transcript.
```Python
def segment_video_from_captions(captions_file):
    with open(captions_file, 'r', encoding='utf-8') as f:
        captions = f.read()
    
    segments = []  # List to store (start, end, text) tuples
    for line in captions.split('\n\n'):
        if line:
            parts = line.split('\n')
            if len(parts) >= 3:
                timestamp = parts[1]
                start, end = timestamp.split(' --> ')
                text = ' '.join(parts[2:])
                segment_file = f"{text[:220]}.mp4"
                segments.append((start.replace(',', '.'), end.replace(',', '.'), segment_file))
                subprocess.run(["ffmpeg", "-i", "video.mp4", "-ss", start, "-to", end, "-an", "-y", segment_file], check=True)
    return segments
```

## Step 3: Generate Audio from Text
Use /tts endpoint to get audio file url that we download.

```Python
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
```


## Step 4: Merge Audio with Video Segments
FFMPEG conates with new audio.

```Python
def generate_and_attach_audio(segments):
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=600, max=100",
    }
    
    for start, end, segment_file in segments:
        text = os.path.splitext(segment_file)[0]
        data = json.dumps({
            "api_key": "YOUR_API_KEY",
            "text": text,
            "voices": "Voice name",
        })
        response = requests.post('https://metavoicexyz--tts-app.modal.run', headers=headers, data=data)
        audio_file = f"{text[:220]}.wav"
        with open(audio_file, 'wb') as f:
            f.write(response.content)
        
        # Convert WAV to the correct format for merging
        sound = AudioSegment.from_wav(audio_file)
        sound.export(audio_file, format="wav", parameters=["-ar", "24000", "-ac", "2"])
        
        # Merge audio and video
        merged_file = f"merged_{segment_file}"
        subprocess.run(["ffmpeg", "-i", segment_file, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", merged_file], check=True)
```


## Step 5: Concatenate Video

```Python

def concatenate_videos(segments):
    with open("filelist.txt", "w") as f:
        for _, _, segment_file in segments:
            f.write(f"file 'merged_{segment_file}'\n")
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "filelist.txt", "-c", "copy", "final_output.mp4"], check=True)

