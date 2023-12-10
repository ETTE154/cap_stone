# %%
import cv2
import pysrt
import os
import pandas as pd
from datetime import datetime
import re
from datetime import timedelta

import base64
import requests
import json
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()

# 필요한 환경 변수를 설정하는 부분
api_key = os.getenv("OPENAI_API_KEY")

# 이미지를 base64로 인코딩하는 함수
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# OpenAI API를 사용하여 이미지 설명을 얻는 함수
def get_image_description(api_key, base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return json.loads(response.text)['choices'][0]['message']['content']


def extract_barrier_free_subtitles(subs):
    return [sub for sub in subs if re.match(r'\[.*?\]', sub.text)]

def srttime_to_timedelta(subrip_time):
    return timedelta(hours=subrip_time.hours, minutes=subrip_time.minutes, 
                     seconds=subrip_time.seconds, milliseconds=subrip_time.milliseconds)

def extract_frames(video_path, subtitle_path, api_key):
    subs = pysrt.open(subtitle_path)
    barrier_free_subs = extract_barrier_free_subtitles(subs)

    cap = cv2.VideoCapture(video_path)

    folder_name = "vision_Rationale"
    os.makedirs(folder_name, exist_ok=True)

    data = []

    for sub in barrier_free_subs:
        start_time = srttime_to_timedelta(sub.start)
        end_time = srttime_to_timedelta(sub.end)
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time.total_seconds() * 1000)
        ret, frame = cap.read()

        if ret:
            time_str = f"{sub.start.hours:02d}{sub.start.minutes:02d}{sub.start.seconds:02d}"
            image_path = f'{folder_name}/{time_str}.jpg'
            cv2.imwrite(image_path, frame)

            # 이미지를 base64로 인코딩하고 설명을 얻습니다
            base64_image = encode_image_to_base64(image_path)
            vision_rationale = get_image_description(api_key, base64_image)

            data.append([sub.start, sub.end, sub.text, image_path, vision_rationale])

    cap.release()
    return pd.DataFrame(data, columns=['Start Time', 'End Time', 'Subtitle', 'Image Path', 'Vision Rationale'])

# 사용 예
df = extract_frames('내가죽던날_자막.mp4', '내가죽던날_자막.srt', api_key)
df.to_csv('extracted_frames.csv', index=False)

# %%
