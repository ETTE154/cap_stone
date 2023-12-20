from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog
from PyQt6.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt6.QtCore import QUrl, QTimer
import sys
import pandas as pd
import requests
import os
from dotenv import load_dotenv

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # GUI 설정
        self.setWindowTitle("진동 데이터 전송")
        layout = QVBoxLayout()
        
        self.videoButton = QPushButton("영상 선택")
        self.videoButton.clicked.connect(self.openVideo)
        layout.addWidget(self.videoButton)

        self.playButton = QPushButton("영상 재생 및 데이터 전송")
        self.playButton.clicked.connect(self.playVideo)
        layout.addWidget(self.playButton)

        self.videoLabel = QLabel("영상 파일: ")
        layout.addWidget(self.videoLabel)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.mediaPlayer = QMediaPlayer()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sendDataToArduino)

        self.videoPath = ""
        self.df = pd.DataFrame()  # DataFrame for analyzed data

        # 환경 변수 로드
        load_dotenv()
        self.arduino_ip = os.getenv("ARDUINO_IP")
        self.arduino_port = os.getenv("ARDUINO_PORT")
        self.arduino_url = f"http://{self.arduino_ip}:{self.arduino_port}"

    def openVideo(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename:
            self.videoPath = filename
            self.videoLabel.setText(f"영상 파일: {filename}")
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))

    def playVideo(self):
        if self.videoPath:
            self.df = pd.read_csv('extracted_frames_with_vibration.csv')  # 분석된 데이터 파일 불러오기
            self.mediaPlayer.play()
            self.timer.start(1000)  # 1초마다 데이터 전송 체크

    def sendDataToArduino(self):
        currentTime = self.mediaPlayer.position()
        for _, row in self.df.iterrows():
            start_time = self.convertToMilliseconds(row['Start_Time'])
            end_time = self.convertToMilliseconds(row['End_Time'])
            if start_time <= currentTime <= end_time:
                duration = end_time - start_time
                vibration_data = row['Vibration_Result']
                self.sendVibrationData(duration, vibration_data)
                break

    def sendVibrationData(self, duration, vibration_data):
        data = {"duration": duration, "vibration": vibration_data}
        response = requests.get(self.arduino_url, params=data)
        print(response.text)

    def convertToMilliseconds(self, time_str):
        h, m, s, ms = map(int, time_str.replace(',', ':').split(':'))
        return (h * 3600 + m * 60 + s) * 1000 + ms

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
