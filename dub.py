import argparse
import concurrent.futures
import json
import os
import re
import requests
import subprocess
from gradio_client import Client
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

# Initialize MetaVoice TTS client
client = Client("https://ttsdemo.themetavoice.xyz/")

def download_video_and_captions(url):
    """Step 1: Download the video and its closed captions using yt-dlp."""
    try:
        subprocess.run(["yt-dlp", "-o", "video.mp4", "--write-auto-sub", "--sub-format", "srt", "--sub-lang", "en", url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download video and captions: {e}", file=sys.stderr)
        exit(1)

def process_captions_and_segment_video(captions_file="video.en.srt"):
    """Step 2: Process captions and segment the video based on captions."""
    segments = []  # List to store (start, end, text) tuples
    with open(captions_file, 'r', encoding='utf-8') as f:
        captions = f.read()

    for line in captions.split('\n\n'):
        if line:
            parts = line.split('\n')
            if len(parts) >= 3:
                timestamp = parts[1]
                start, end = timestamp.split(' --> ')
                text = ' '.join(parts[2:])
                segment_file = f"segment_{start.replace(':', '').replace(',', '')}.mp4"
                segments.append((start.replace(',', '.'), end.replace(',', '.'), text[:220], segment_file))
                subprocess.run(["ffmpeg", "-i", "video.mp4", "-ss", start, "-to", end, "-an", "-y", segment_file], check=True)
    return segments

def generate_tts(text):
    """Generate TTS for a given text."""
    result = client.predict(
        text, 0.0, 1.0, "Preset voices", "Bria",
        "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav",
        api_name="/tts"
    )
    return result

def generate_and_attach_audio(segments):
    """Step 3 & 4: Generate audio from text and merge with video segments."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_segment = {executor.submit(generate_tts, segment[2]): segment for segment in segments}
        
        for future in concurrent.futures.as_completed(future_to_segment):
            segment = future_to_segment[future]
            start, end, text, segment_file = segment
            try:
                result = future.result()
                audio_url = result['audio_url']  # Assuming the result dict contains an 'audio_url'
                audio_file = f"{segment_file.rsplit('.', 1)[0]}.wav"
                # Download the audio file
                response = requests.get(audio_url)
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                # Merge audio and video
                merged_file = f"merged_{segment_file}"
                subprocess.run(["ffmpeg", "-i", segment_file, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", merged_file], check=True)
            except Exception as exc:
                print(f"Failed to generate or attach audio for {text}: {exc}")

def concatenate_videos(segments):
    """Step 5: Concatenate all video segments into a final video."""
    with open("filelist.txt", "w") as f:
        for _, _, _, segment_file in segments:
            merged_file = f"merged_{segment_file}"
            if os.path.exists(merged_file):
                f.write(f"file '{merged_file}'\n")
    
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "filelist.txt", "-c", "copy", "final_output.mp4"], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change a YouTuber's voice using MetaVoice TTS.")
    parser.add_argument("-u", "--url", required=True, help="URL of the YouTube video to process")
    args = parser.parse_args()

    download_video_and_captions(args.url)
    segments = process_captions_and_segment_video()
    generate_and_attach_audio(segments)
    concatenate_videos(segments)
    print("Process completed. Final video is 'final_output.mp4'.")
