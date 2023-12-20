# %%
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import requests
import os
from dotenv import load_dotenv
import vlc

class MainWindow:
    def __init__(self, window):
        self.window = window
        window.title("진동 데이터 전송")

        self.openVideoButton = tk.Button(window, text="영상 선택", command=self.openVideo)
        self.openVideoButton.pack()

        self.playButton = tk.Button(window, text="영상 재생 및 데이터 전송", command=self.playVideo)
        self.playButton.pack()

        self.videoLabel = tk.Label(window, text="영상 파일: ")
        self.videoLabel.pack()

        self.df = pd.DataFrame()  # DataFrame for analyzed data

        # 환경 변수 로드
        load_dotenv()
        self.arduino_ip = os.getenv("ARDUINO_IP")
        self.arduino_port = os.getenv("ARDUINO_PORT")
        self.arduino_url = f"http://{self.arduino_ip}:{self.arduino_port}"
        self.videoPath = ""
        self.player = None

    def openVideo(self):
        self.videoPath = filedialog.askopenfilename(title="Open Video", filetypes=[("Video Files", "*.mp4 *.avi")])
        if self.videoPath:
            self.videoLabel.config(text=f"영상 파일: {self.videoPath}")

    def playVideo(self):
        if not self.videoPath:
            messagebox.showerror("Error", "영상 파일을 선택해주세요.")
            return

        self.df = pd.read_csv('extracted_frames_with_vibration.csv')  # 분석된 데이터 파일 불러오기
        self.initVLCPlayer()

    def initVLCPlayer(self):
        if self.player:
            self.player.stop()

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        media = self.instance.media_new(self.videoPath)
        self.player.set_media(media)

        # Tkinter에서 VLC 플레이어 바인딩
        self.player.set_hwnd(self.window.winfo_id())
        self.player.play()
        self.updateFrame()

    def updateFrame(self):
        if self.player.is_playing():
            currentTime = self.player.get_time()
            self.sendDataToArduino(currentTime)
            self.window.after(500, self.updateFrame)  # 0.5초마다 체크

    def sendDataToArduino(self, currentTime):
        for _, row in self.df.iterrows():
            start_time = self.convertToMilliseconds(row['Start_Time'])
            end_time = self.convertToMilliseconds(row['End_Time'])
            if start_time <= currentTime <= end_time:
                duration = end_time - start_time
                vibration_data = row['Vibration_Result']
                self.sendVibrationData(duration, vibration_data)
                break


    def onClose(self):
        if self.player is not None:
            self.player.stop()
        self.window.destroy()

# 메인 실행 부분
if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", main_window.onClose)
    root.mainloop()
