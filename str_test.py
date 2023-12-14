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

client = OpenAI()

load_dotenv()

# 필요한 환경 변수를 설정하는 부분
api_key = os.getenv("OPENAI_API_KEY")

#%%
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

    folder_name = "Rationale"
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
    return pd.DataFrame(data, columns=['Start_Time', 'End_Time', 'Text_Rationale', 'Image_Path', 'Vision_Rationale'])

# 사용 예
df = extract_frames('내가죽던날_자막.mp4', '내가죽던날_자막.srt', api_key)
df.to_csv('extracted_frames.csv', index=False)

#%%
from openai import OpenAI
import re

def get_vibration_pattern(text_rationale, vision_rationale):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Analyze the movie scene based on the barrier-free subtitle and image description and suggest a suitable vibration pattern."},
            {"role": "user", "content": f"장면의 배리어 프리 자막은 '{text_rationale}'"},
            {"role": "user", "content": f"장면에 대한 설명은 '{vision_rationale}'."},
            {"role": "system", "content": "The vibration pattern should be one of 0 (increasing intensity), 1 (decreasing intensity), or 2 (constant intensity). What is the vibration pattern? (0, 1, or 2)"}
        ]
    )

    # 정규 표현식 필터
    filter = re.compile(r'0|1|2')
    
    # response에서 content 속성 추출
    content = response.choices[0].message.content

    # content에서 숫자 찾기
    match = filter.findall(content)

    # 첫 번째 일치 항목을 정수로 변환
    return int(match[0]) if match else None

def get_vibration_min_intensity(text_rationale, vision_rationale, vibration_pattern):
    client = OpenAI()
    if vibration_pattern == 0:
        v_pattern = "increasing"
    elif vibration_pattern == 1:
        v_pattern = "decreasing"
    elif vibration_pattern == 2:
        v_pattern = "constant"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Analyze the movie scene based on the barrier-free subtitle and image description and suggest a suitable vibration pattern."},
            {"role": "user", "content": f"장면의 배리어 프리 자막은 '{text_rationale}'"},
            {"role": "user", "content": f"장면에 대한 설명은 '{vision_rationale}'."},
            {"role": "system", "content": f"{vibration_pattern}의 형태를 가지는 진동을 발생할때, 진동의 최소 강도는 얼마인가요? (0에서 10 사이의 숫자를 입력하세요.)"}
        ]
    )

    # 정규 표현식 필터
    filter = re.compile(r'0|1|2|3|4|5|6|7|8|9|10')
    
    # response에서 content 속성 추출
    content = response.choices[0].message.content

    # content에서 숫자 찾기
    match = filter.findall(content)

    # 첫 번째 일치 항목을 정수로 변환
    return int(match[0]) if match else None

def get_vibration_max_intensity(text_rationale, vision_rationale, vibration_pattern, vibration_min_intensity):
    client = OpenAI()
    if vibration_pattern == 0:
        v_pattern = "increasing"
    elif vibration_pattern == 1:
        v_pattern = "decreasing"
    elif vibration_pattern == 2:
        v_pattern = "constant"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Analyze the movie scene based on the barrier-free subtitle and image description and suggest a suitable vibration pattern."},
            {"role": "user", "content": f"장면의 배리어 프리 자막은 '{text_rationale}'"},
            {"role": "user", "content": f"장면에 대한 설명은 '{vision_rationale}'."},
            {"role": "system", "content": f"{vibration_pattern}의 형태를 가지는 진동을 발생할때, 진동의 최소 강도가 {vibration_min_intensity}이면 진동의 최대 강도는 얼마인가요? (0에서 10 사이의 숫자를 입력하세요.)"}
        ]
    )

    # 정규 표현식 필터
    filter = re.compile(r'0|1|2|3|4|5|6|7|8|9|10')
    
    # response에서 content 속성 추출
    content = response.choices[0].message.content

    # content에서 숫자 찾기
    match = filter.findall(content)

    # 첫 번째 일치 항목을 정수로 변환
    return int(match[0]) if match else None


# 결과
vibration_pattern = get_vibration_pattern(df['Text_Rationale'][7], df['Vision_Rationale'][7])
min_intensity = get_vibration_min_intensity(df['Text_Rationale'][7], df['Vision_Rationale'][7], vibration_pattern)
max_intensity = get_vibration_max_intensity(df['Text_Rationale'][7], df['Vision_Rationale'][7], vibration_pattern, min_intensity)
result_list = [vibration_pattern, min_intensity, max_intensity]
print(result_list)
#%%
from openai import OpenAI
client = OpenAI()
df = pd.read_csv('extracted_frames.csv')
class VibrationPatternExtractor:
    # 생성자
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI()
        
    # 패턴 추출 함수
    def extract_vibration_pattern(text_rationale, vision_rationale):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "이 영화 장면을 분석하고, 장애물 없는 자막과 이미지 설명을 바탕으로 진동 패턴 번호(0, 1, 2)를 제안하세요."},
                {"role": "user", "content": f"이 장면의 장애물 없는 자막은 '{text_rationale}'이고, 이미지 설명은 '{vision_rationale}'입니다."},
                {"role": "system", "content": "패턴 번호는 0(점점 증가하는 강도), 1(점점 감소하는 강도), 또는 2(일정한 강도) 중 하나여야 합니다. 패턴 번호는 무엇입니까? (0, 1, 2 중 하나)"}
            ]
        )
        pattern_message = response.choices[0].message if response.choices else "No response"
        pattern = pattern_message.strip() if isinstance(pattern_message, str) else None
        return int(pattern) if pattern and pattern.isdigit() else None

    # 최소 강도 추출 함수
    def extract_min_intensity(text_rationale, vision_rationale):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "이 영화 장면을 분석하고, 장애물 없는 자막과 이미지 설명을 바탕으로 진동 패턴의 최소 강도 수준(0에서 10 사이)을 제안하세요."},
                {"role": "user", "content": f"이 장면의 장애물 없는 자막은 '{text_rationale}'이고, 이미지 설명은 '{vision_rationale}'입니다."},
                {"role": "system", "content": "최소 강도 수준은 0에서 10 사이의 숫자여야 합니다. 최소 강도 수준은 얼마입니까?(예시 : 0))"}
            ]
        )
        min_intensity_message = response.choices[0].message if response.choices else "No response"
        min_intensity = min_intensity_message.strip() if isinstance(min_intensity_message, str) else None
        return int(min_intensity) if min_intensity and min_intensity.isdigit() else None

    # 최대 강도 추출 함수
    def extract_max_intensity(text_rationale, vision_rationale):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "이 영화 장면을 분석하고, 장애물 없는 자막과 이미지 설명을 바탕으로 진동 패턴의 최대 강도 수준(0에서 10 사이)을 제안하세요."},
                {"role": "user", "content": f"이 장면의 장애물 없는 자막은 '{text_rationale}'이고, 이미지 설명은 '{vision_rationale}'입니다."},
                {"role": "system", "content": "최대 강도 수준은 0에서 10 사이의 숫자여야 합니다. 최대 강도 수준은 얼마입니까?(예시 : 10)"}
            ]
        )
        max_intensity_message = response.choices[0].message if response.choices else "No response"
        max_intensity = max_intensity_message.strip() if isinstance(max_intensity_message, str) else None
        return int(max_intensity) if max_intensity and max_intensity.isdigit() else None

# 예시 결과 추출을 위한 코드
text_rationale_example = df['Text_Rationale'][7]
vision_rationale_example = df['Vision_Rationale'][7]

pattern = VibrationPatternExtractor.extract_vibration_pattern(text_rationale_example, vision_rationale_example)
min_intensity = VibrationPatternExtractor.extract_min_intensity(text_rationale_example, vision_rationale_example)
max_intensity = VibrationPatternExtractor.extract_max_intensity(text_rationale_example, vision_rationale_example)

# 결과 리스트
result_list = [pattern, min_intensity, max_intensity]
result_list


# %%
vision_rationale_example
# %%
