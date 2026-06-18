# Remote-Controlled Tactical Rover

An AI-powered autonomous ground robot prototype for human detection and tactical engagement, built on a **Raspberry Pi (vision + driving)** and **Arduino Nano (turret + firing)** dual-controller architecture, with a phone/browser-based live control dashboard.

**Course:** CSE 4326 — Final Project
**Team:** Group Three
**Institution:** United International University (UIU)

---

## Team Members

| Name |
|---|
| Adnan Mohammad Salauddin |
| Easmin Akter Tule |
| Taki Tahmid |
| Somaya Tabassum |
| Shamim |

---

## Project Overview

Tactical ground robotics is still an underdeveloped area in Bangladesh's local research and academic space, despite rapid global progress in autonomous defense platforms. This project is a proof-of-concept built to show that real-time human detection, autonomous engagement logic, and precision mobility can all be achieved on **low-cost, accessible hardware** — a Raspberry Pi and an Arduino Nano — instead of expensive, closed, imported systems.

The rover combines:

- A **2WD differential-drive chassis** (Raspberry Pi + `gpiozero` motor control) for movement
- A **YOLOv8-based human detection pipeline** running on the Raspberry Pi for real-time AI vision
- A **4-servo turret + flywheel/ESC firing mechanism** controlled by an Arduino Nano
- A **Flask-based web dashboard** for live MJPEG video streaming and manual/auto mode control
- A **Serial (UART) link between Pi and Nano** that sends the fire command only when a human is confirmed and the system is in AUTO mode
- An **LCD status display and buzzer** on the turret unit for local visual/audio feedback during target lock and firing

---

## Key Features

- **Autonomous Human Detection & Firing** — Pi runs YOLOv8 on the live camera feed; on confirmed human detection in AUTO mode, it sends a fire command to the Arduino over serial.
- **Browser-Based Remote Control Interface** — Live camera feed, directional controls, AUTO/MANUAL toggle, adjustable speed (10%–100%), and emergency stop, all from a phone or PC browser.
- **Differential-Drive Movement** — Forward, backward, left, right via two independently controlled DC motors.
- **Pan-Scan Turret with Auto-Fire Sequence** — Continuously sweeping servos for scanning; on a fire command, the turret locks, fires, resets, and resumes scanning.
- **Manual Override Mode** — Operator can fully drive the rover via keyboard arrow keys or on-screen buttons at any time.
- **Emergency Stop** — Instantly halts all motor movement regardless of current mode.

---

## System Architecture

```
                ┌────────────────────────┐
                │   Operator's Browser     │
                │ (Phone / PC Dashboard)    │
                └───────────┬─────────────┘
                          HTTP (Flask routes)
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │           RASPBERRY PI                 │
        │  - Flask web server (control + video)   │
        │  - Picamera2 video capture                │
        │  - YOLOv8n human detection (ai_loop)      │
        │  - Drive motor control (gpiozero)          │
        │  - Mode logic: AUTO / MANUAL / E-STOP        │
        └───────────────┬───────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
   ┌─────────────────────┐  ┌─────────────────────────┐
   │  Left/Right DC Motors │  │  Serial (UART) → 'F'/'f'  │
   │  (gpiozero.Motor)      │  │  sent only when:            │
   │  Forward/Backward/      │  │  mode == AUTO AND            │
   │  Left/Right/Stop          │  │  human_detected == True       │
   └─────────────────────┘  └───────────┬─────────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │        ARDUINO NANO            │
                          │  - Listens on Serial for 'F'/'f' │
                          │  - Servo1 & Servo4: scanning      │
                          │    sweep (continuous, idle)        │
                          │  - Servo2: nodding sweep              │
                          │  - On fire command → fireSequence():   │
                          │    buzzer ON → LCD "HUMAN DETECTED"      │
                          │    → ESC to MAX (trigger/flywheel) →      │
                          │    Servo3 fires (0°→180°) → ESC resets →    │
                          │    buzzer OFF → LCD "FIRE COMPLETE"          │
                          │  - LCD (16x2 I2C): live status display        │
                          └─────────────────────────────────────────────┘
```

**Key design point:** the Raspberry Pi handles *perception and locomotion*; the Arduino Nano handles *aiming and firing*. They are deliberately decoupled — the Pi never controls the servos/ESC directly, it only sends a single-character serial trigger (`'F'`/`'f'`) once AI detection and the AUTO-mode/safety condition are both satisfied. This keeps the firing subsystem isolated, predictable, and easy to safety-gate independently of the vision/driving code.

---

## Hardware Components

| Component | Role | Connected To |
|---|---|---|
| **Raspberry Pi** | Main controller — runs AI detection, web server, video streaming, drive motor control | Camera, drive motors, Arduino Nano (via Serial/UART) |
| **Raspberry Pi Camera (Picamera2)** | Live video capture for both streaming and YOLO inference | Raspberry Pi (CSI camera port) |
| **2x DC Motors + Motor Driver** | Differential drive — forward/backward/left/right | Raspberry Pi GPIO pins 17, 27 (left), 22, 23 (right) |
| **Arduino Nano** | Turret controller — handles scanning, aiming, and firing sequence | Serial (RX/TX) to Raspberry Pi |
| **Servo 1 & Servo 4** | Mirror-linked horizontal scanning sweep (idle/scan motion) | Arduino Nano pins D3, D4 |
| **Servo 2** | Vertical nodding sweep (idle/scan motion) | Arduino Nano pin D5 |
| **Servo 3** | Fire-trigger actuator (0°→180° on fire command) | Arduino Nano pin D6 |
| **ESC (Electronic Speed Controller)** | Drives the flywheel/launcher motor for firing | Arduino Nano pin D10 |
| **Buzzer** | Audio alert during target lock and firing sequence | Arduino Nano pin D11 |
| **16x2 I2C LCD Display** | Local status readout: scanning, human detected, target locked, fire complete | Arduino Nano (I2C, address 0x27) |

> ⚠️ Note: an earlier draft of this README described an ESP32-based design. The actual implemented system uses a **Raspberry Pi + Arduino Nano**, as reflected above and in the firmware/software code in this repository.

---

## Software Stack

| Layer | Technology |
|---|---|
| AI / Computer Vision | Python, [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (`yolov8n.pt`), OpenCV |
| Camera Capture | `picamera2` |
| Drive Motor Control | `gpiozero.Motor` |
| Web Server / Dashboard | Flask (`Response`, MJPEG streaming, HTML/JS served via `render_template_string`) |
| Pi ↔ Arduino Communication | Serial / UART (single-character commands, e.g. `'F'`/`'f'` to trigger fire) |
| Turret Firmware | Arduino (C++), `Servo.h`, `Wire.h`, `LiquidCrystal_I2C.h` |
| Frontend Controls | Vanilla HTML/CSS/JS — keyboard (arrow keys, number keys) and on-screen buttons |

---

## Repository Structure

```
tactical-rover/
├── pi/
│   └── app.py                  # Flask server, YOLO detection loop, motor control, video stream
├── arduino/
│   └── turret_controller.ino   # Servo scanning, fire sequence, LCD + buzzer status, serial listener
├── docs/
│   └── images/                 # Project photos, diagrams, screenshots (see Project_Report.pdf)
├── Project_Report.pdf          # Final IEEE-format project report
└── README.md                    # This file
```

> 📌 Update folder/file names above if your actual repo layout differs.

---

## Getting Started

### Prerequisites

**Raspberry Pi side:**
- Raspberry Pi (with Raspberry Pi OS, camera module enabled)
- Python 3.x with the following packages:
  ```bash
  pip install flask gpiozero ultralytics opencv-python picamera2
  ```

**Arduino side:**
- Arduino IDE
- Libraries: `Servo.h` (built-in), `Wire.h` (built-in), `LiquidCrystal_I2C` (install via Library Manager)
- Arduino Nano board

### Wiring Summary

| Pi GPIO | Function | Arduino Pin | Function |
|---|---|---|---|
| 17, 27 | Left motor (fwd/back) | D3 | Servo 1 (scan mirror) |
| 22, 23 | Right motor (fwd/back) | D4 | Servo 4 (scan sweep) |
| TX/RX | Serial to Arduino | D5 | Servo 2 (nod sweep) |
| — | — | D6 | Servo 3 (fire trigger) |
| — | — | D10 | ESC (launcher motor) |
| — | — | D11 | Buzzer |
| — | — | I2C (A4/A5) | 16x2 LCD (0x27) |

> ⚠️ Double-check your actual Pi GPIO ↔ Arduino serial wiring (TX→RX, RX→TX, common GND) before powering on.

### Running the Project

**1. Flash the Arduino Nano:**
```bash
# Open arduino/turret_controller.ino in Arduino IDE
# Select Board: Arduino Nano, correct COM port
# Upload
```

**2. Start the Raspberry Pi controller:**
```bash
cd pi
python3 app.py
```
The server starts on `http://<raspberry-pi-ip>:5000`.

**3. Open the dashboard:**
- On your phone or PC browser, navigate to `http://<raspberry-pi-ip>:5000`
- Live video feed loads automatically
- Use **AUTO** / **MANUAL** buttons to switch modes
- Use arrow keys or on-screen buttons to drive in MANUAL mode
- Use number keys (1–0) or speed buttons to adjust speed (10%–100%)
- Use **STOP** for emergency stop at any time

---

## Operation Modes

1. **AUTO Mode** — The Pi continuously runs YOLOv8 on the live camera feed. If a person (`class 0`) is detected with confidence > 0.6, the rover stops and sends a fire command (`'F'`) to the Arduino over serial, which runs the turret's fire sequence (buzzer + LCD alert → trigger servo + ESC launcher → reset → scan resumes). If no human is detected, the rover continues driving forward.
2. **MANUAL Mode** — The operator drives the rover directly using arrow keys/buttons from the web dashboard; the AI loop keeps running in the background but does not control the motors.
3. **Emergency Stop** — Immediately halts all drive motors and overrides both AUTO and MANUAL command execution until cleared by switching modes again.

On the Arduino side, the turret independently runs a continuous scanning sweep (Servo 1/2/4) at all times and only triggers the `fireSequence()` routine when it receives an `'F'`/`'f'` byte over serial from the Pi.

---

## Demo Video

📺 **Video Demonstration:** `<insert your YouTube or Google Drive demo video link here>`

---

## Project Report

📄 Full IEEE-format project report: [`Project_Report.pdf`](./Project_Report.pdf)

---

## Limitations

- Human-detection accuracy (YOLOv8n at 256px inference size) is sensitive to lighting conditions, distance, and background clutter.
- The Pi↔Arduino serial link and the Flask web dashboard are both unencrypted/unauthenticated on the local network.
- Perception relies solely on the Pi camera, with no sensor fusion (depth/radar/ultrasonic) for obstacle avoidance.
- Fire confirmation is based on a single-frame confidence threshold (0.6) rather than multi-frame tracking, which can be sensitive to momentary false positives.

## Future Work

- Multi-frame target confirmation and tracking to reduce false-positive fire triggers.
- Sensor fusion (ultrasonic/depth) for obstacle avoidance during autonomous driving.
- Authentication and encryption for the web dashboard and serial link.
- Migrating the fixed AUTO-fire logic to include a configurable digital arm/disarm safety switch on the dashboard itself (currently mode-gated only).

---

## License

`<specify your license here, e.g., MIT License — or state "Academic project, CSE 4326, UIU">`

---

## Acknowledgment

This project was developed as part of the CSE 4326 course at United International University (UIU), under the guidance of the course instructor.