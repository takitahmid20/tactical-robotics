from flask import Flask, Response, render_template_string
from gpiozero import Motor
from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import threading
import time
import serial  # আরডুইনোর সাথে যোগাযোগের জন্য যোগ করা হলো

# ================= FLASK =================
app = Flask(__name__)

# ================= SPEED =================
SPEED = 0.5

def set_speed(val):
    global SPEED
    SPEED = max(0.1, min(1.0, val))
    print(f"[SPEED] {int(SPEED * 100)}%")

    # apply immediately in manual mode
    if mode == "manual" and not emergency_stop:
        apply_command()

# ================= GLOBAL STATE =================
mode = "manual"
current_command = "stop"
latest_frame = None
emergency_stop = False

# ================= SERIAL SETUP (ARDUINO) =================
# আপনার আরডুইনোর সঠিক পোর্টটি এখানে দিন (যেমন: /dev/ttyUSB0 অথবা /dev/ttyACM0)
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2) # সিরিয়াল কানেকশন স্থিতিশীল হওয়ার জন্য ২ সেকেন্ড বিরতি
    print("🔌 ARDUINO CONNECTED SUCCESSFULLY!")
except Exception as e:
    print(f"⚠️ ARDUINO CONNECTION FAILED: {e}")
    arduino = None

# ================= MOTOR SETUP =================
motor_left = Motor(forward=17, backward=27, pwm=True)
motor_right = Motor(forward=22, backward=23, pwm=True)

# ================= CAMERA =================
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (480, 360)}
    )
)
picam2.start()
time.sleep(2)

# ================= YOLO =================
model = YOLO("yolov8n.pt")

print("🚗 SYSTEM STARTED")

# ================= MOTOR CONTROL =================
def stop():
    motor_left.stop()
    motor_right.stop()
    print("STOP")

def forward():
    motor_left.forward(SPEED)
    motor_right.forward(SPEED)
    print(f"FORWARD {int(SPEED * 100)}%")

def backward():
    motor_left.backward(SPEED)
    motor_right.backward(SPEED)
    print(f"BACKWARD {int(SPEED * 100)}%")

def left():
    motor_left.backward(SPEED)
    motor_right.forward(SPEED)
    print(f"LEFT {int(SPEED * 100)}%")

def right():
    motor_left.forward(SPEED)
    motor_right.backward(SPEED)
    print(f"RIGHT {int(SPEED * 100)}%")

def fire():
    print("🔥 FIRE TRIGGERED")
    if arduino is not None:
        try:
            arduino.write(b'f') # আরডুইনোকে ফায়ারিং ক্যারেক্টার পাঠানো হচ্ছে
            print("🚀 Fire command sent to Arduino!")
        except Exception as e:
            print(f"Error sending serial data: {e}")
    else:
        print("⚠️ Cannot fire! Arduino not connected via Serial.")

# ================= APPLY COMMAND =================
def apply_command():
    global current_command

    if mode != "manual":
        return

    if current_command == "forward":
        forward()
    elif current_command == "backward":
        backward()
    elif current_command == "left":
        left()
    elif current_command == "right":
        right()
    else:
        stop()

# ================= AI LOOP =================
def ai_loop():
    global latest_frame, mode, current_command, emergency_stop

    while True:
        frame = picam2.capture_array()
        if frame is None:
            continue

        results = model(frame, verbose=False, imgsz=256)

        human_detected = False

        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.6:
                    human_detected = True
                    break

        # ================= AUTO MODE =================
        if mode == "auto" and not emergency_stop:
            if human_detected:
                stop()
                fire()
                time.sleep(2) # এক টানা ফায়ারিং আটকাতে ২ সেকেন্ড সেফটি পজ দেওয়া হলো
            else:
                forward()

        # ================= MANUAL MODE =================
        elif mode == "manual" and not emergency_stop:
            apply_command()

        # ================= EMERGENCY STOP =================
        if emergency_stop:
            stop()

        latest_frame = frame.copy()
        time.sleep(0.03)

# ================= HTML =================
# ড্যাশবোর্ডে একটি ডেডিকেটেড লাল রঙের FIRE বাটন এবং কীবোর্ডের 'Spacebar' দিয়ে কন্ট্রোল যোগ করা হলো
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>PI ROBOT</title>

<style>
body{margin:0;background:#0d1117;color:white;font-family:Arial;text-align:center;}
.header{padding:15px;background:#161b22;font-size:20px;font-weight:bold;}
img{width:90%;border-radius:10px;border:2px solid #2ea043;margin-top:10px;}
.panel{margin-top:15px;display:grid;grid-template-columns:repeat(3,100px);gap:10px;justify-content:center;}
button{padding:12px;border-radius:10px;border:none;cursor:pointer;background:#238636;color:white;font-weight:bold;}
.stop{background:#da3633;}
.mode{background:#1f6feb;}
.speed{background:#f39c12;}
.fire-btn{background:#ff3333; grid-column: span 3; font-size: 18px; margin-top: 5px; box-shadow: 0 0 10px rgba(255,51,51,0.5);}
.fire-btn:active{background:#b30000;}
</style>
</head>

<body>

<div class="header">PI ROBOT CONTROL</div>

<img src="/video_feed">

<div class="panel">

<button onclick="send('a')" class="mode">AUTO</button>
<button onclick="send('m')" class="mode">MANUAL</button>
<button onclick="send('stop')" class="stop">STOP</button>

<button onclick="speed(0.1)" class="speed">10%</button>
<button onclick="speed(0.5)" class="speed">50%</button>
<button onclick="speed(1.0)" class="speed">100%</button>

<button onclick="send('fire')" class="fire-btn">🔥 SHOOT !!!</button>

</div>

<script>

document.addEventListener('keydown', function(e){
    if(e.key === ' ' || e.code === 'Space') {
        e.preventDefault(); // স্পেসবার চাপলে পেজ স্ক্রোল হওয়া আটকাবে
        send('fire');
    } else {
        send(e.key);
    }

    if(e.key==='1') speed(0.1);
    if(e.key==='2') speed(0.2);
    if(e.key==='3') speed(0.3);
    if(e.key==='4') speed(0.4);
    if(e.key==='5') speed(0.5);
    if(e.key==='6') speed(0.6);
    if(e.key==='7') speed(0.7);
    if(e.key==='8') speed(0.8);
    if(e.key==='9') speed(0.9);
    if(e.key==='0') speed(1.0);
});

function send(k){
    fetch('/control/' + k);
}

function speed(v){
    fetch('/speed/' + v);
}

</script>

</body>
</html>
"""

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/control/<key>")
def control(key):
    global mode, current_command, emergency_stop

    if key == "stop":
        emergency_stop = True
        current_command = "stop"
        stop()
        print("EMERGENCY STOP")

    elif key == "fire":
        fire()

    elif key.lower() == "a":
        mode = "auto"
        emergency_stop = False
        stop()

    elif key.lower() == "m":
        mode = "manual"
        emergency_stop = False
        stop()

    if mode == "manual" and not emergency_stop:
        if key == "ArrowUp":
            current_command = "forward"
        elif key == "ArrowDown":
            current_command = "backward"
        elif key == "ArrowLeft":
            current_command = "left"
        elif key == "ArrowRight":
            current_command = "right"

    return "OK"

@app.route("/speed/<val>")
def speed(val):
    set_speed(float(val))
    return "OK"

# ================= VIDEO STREAM =================
def generate_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            continue

        frame = cv2.cvtColor(latest_frame, cv2.COLOR_RGB2BGR)

        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
              buffer.tobytes() + b"\r\n")

        time.sleep(0.03)

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# ================= START =================
threading.Thread(target=ai_loop, daemon=True).start()

app.run(host="0.0.0.0", port=5000, threaded=True)
