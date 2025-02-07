from flask import Flask, render_template
from flask_socketio import SocketIO
import serial
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# **Serial 포트 설정 (환경에 맞게 수정)**
SERIAL_PORT = "COM5"  # Windows: COM6 / Mac, Linux: "/dev/ttyUSB0"
BAUD_RATE = 9600

# **기존 Serial 연결이 있으면 닫기**
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"{SERIAL_PORT} 포트가 정상적으로 열렸습니다.")
except serial.SerialException as e:
    print(f"⚠️ 시리얼 포트 오류: {e}")

# **시리얼 데이터 읽는 함수**
def read_serial():
    """STM32에서 데이터를 읽고 WebSocket으로 전송"""
    while True:
        try:
            if ser and ser.is_open:
                data = ser.readline().decode().strip()  # 데이터 읽기
                if data.startswith("COUNT:"):
                    count = int(data.split(":")[1])  # "COUNT:123" -> 123
                    socketio.emit("update_count", {"count": count})  # 웹으로 데이터 전송
        except serial.SerialException as e:
            print(f"⚠️ Serial read error: {e}")
            break  # 에러 발생 시 루프 종료

# **백그라운드에서 Serial 데이터 읽는 스레드 실행**
threading.Thread(target=read_serial, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    try:
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
    finally:
        # **Flask 종료 시 Serial 포트 닫기**
        if ser and ser.is_open:
            ser.close()
            print(f"{SERIAL_PORT} 포트가 닫혔습니다.")
