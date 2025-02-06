from flask import Flask, render_template, jsonify, request
import serial
import serial.tools.list_ports
import threading
import time

app = Flask(__name__)

# ✅ 시리얼 포트 자동 검색
def get_serial_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "COM" in port.device:
            return port.device
    return None

# ✅ 시리얼 포트 설정 (첫 번째 실행만)
SERIAL_PORT = "COM5"
BAUD_RATE = 115200

ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ 시리얼 포트 {SERIAL_PORT}가 정상적으로 열렸습니다.")
    except serial.SerialException as e:
        print(f"🚨 시리얼 포트 {SERIAL_PORT}를 열 수 없습니다: {e}")
        ser = None

current_status = "정지"

# ✅ 시리얼 데이터를 읽는 쓰레드 실행
def read_serial():
    global current_status
    while True:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode().strip()
                if data:
                    if data == "1":
                        current_status = "전진"
                    elif data == "2":
                        current_status = "후진"
                    elif data == "0":
                        current_status = "정지"
            except Exception as e:
                print(f"🚨 시리얼 읽기 오류: {e}")
        time.sleep(0.1)

serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

@app.route('/')
def index():
    return render_template('index.html', status=current_status)

@app.route('/send', methods=['POST'])
def send_command():
    global current_status
    command = request.json.get('command')

    if ser and ser.is_open:
        try:
            ser.write(command.encode())  # 시리얼로 데이터 전송
            print(f"📤 {command} 전송됨")
        except Exception as e:
            print(f"🚨 시리얼 전송 오류: {e}")

    if command == "1":
        current_status = "전진"
    elif command == "2":
        current_status = "후진"
    elif command == "0":
        current_status = "정지"

    return jsonify({"status": current_status})

@app.route('/status')
def get_status():
    return jsonify({"status": current_status})

# ✅ 두 번 실행되지 않도록 보호!
if __name__ == '__main__':
    app.run(debug=True)
