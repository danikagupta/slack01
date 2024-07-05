import assemblyai as aai
from datetime import datetime
import pandas as pd
import yt_dlp as youtube_dl
import time

import os

max_retries = 3
delay = 2

class MyLogger(object):
    def __init__(self, external_logger=lambda x: None):
        self.external_logger = external_logger

    def debug(self, msg):
        print("[debug]: ", msg)
        self.external_logger(msg)

    def warning(self, msg):
        print("[warning]: ", msg)

    def error(self, msg):
        print("[error]: ", msg)


def my_hook(d):
    print("hook", d["status"])
    if d["status"] == "finished":
        print("Done downloading, now converting ...")



def current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_ydl_opts(external_logger=lambda x: None):
    return {
    "format": "bestaudio/best",
    "verbose": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
                "preferredquality": "192",  # set the preferred bitrate to 192kbps
            }
        ],
        "logger": MyLogger(external_logger),
    "outtmpl": "./downloads/audio/%(title)s.%(ext)s",  # Set the output filename directly
    "progress_hooks": [my_hook],
}

def download_video_audio(url, external_logger=lambda x: None):
    retries = 0
    while retries < max_retries:
        try:
            ydl_opts = get_ydl_opts(external_logger)
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                print("Going to download ", url)
                info = ydl.extract_info(url, download=False)
                filesize = info.get("filesize", 0)
                print(f"Download YouTube Filesize: {filesize}")
                filename = ydl.prepare_filename(info)
                res = ydl.download([url])
                print("youtube-dl result :", res)
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                print('mp3 file name - ', mp3_filename)
                return mp3_filename
        except Exception as e:
            retries += 1
            print(
                f"An error occurred during downloading (Attempt {retries}/{max_retries}):",
                str(e),
            )
            if retries >= max_retries:
                raise e
            time.sleep(delay)

def transcribe_yt_assembly2(url,assembly_api_key):
    aai.settings.api_key = assembly_api_key
    
    config = aai.TranscriptionConfig(
     speaker_labels=True,
    )
    transcript = aai.Transcriber().transcribe(url, config)
    return transcript

def save_transcript(ts):
    df=pd.DataFrame(columns=["start","duration","speaker","text"])
    for t in ts:
        duration=(t.end-t.start)/1000
        df.loc[len(df)]=[t.start//1000,duration,t.speaker,t.text]
    #df.to_csv(file_path,index=False)
    #
    # We still need code here to save the transcript back to Google Firestore.
    #

def transcribe_session(youtube_link,assembly_api_key):
    #st.write(f"{current_time()} About to fetch audio from URL {youtube_link}")
    audio_file = download_video_audio(youtube_link)
    #st.write(f"{current_time()} Transcribing audio from URL {youtube_link} file: {audio_file}")
    transcript = transcribe_yt_assembly2(audio_file,assembly_api_key)
    #st.write(f"{current_time()} Completed transcribing {youtube_link}")
    if transcript.status == aai.TranscriptStatus.error:
        return f"Error transcribing audio: {transcript.error}"
    else:
        save_transcript(transcript.utterances)
        msg=""
        for utterance in transcript.utterances:
            duration=(utterance.end-utterance.start)/1000
            msg=msg+f"{utterance.start//1000} - {duration} : Speaker {utterance.speaker}: {utterance.text}\n"
        return msg

