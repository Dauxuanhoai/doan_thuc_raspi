#!/usr/bin/env bash
set -e

sudo apt update
sudo apt install -y \
  python3-pip \
  python3-venv \
  python3-pyqt6 \
  python3-opencv \
  python3-numpy \
  python3-pil \
  python3-openpyxl \
  python3-picamera2 \
  opencv-data \
  rpicam-apps

python3 - <<'PY'
import cv2
print("OpenCV:", cv2.__version__)
try:
    from picamera2 import Picamera2
    print("Picamera2: ok")
except Exception as exc:
    print("Picamera2:", exc)
PY

echo "Cai dat xong. Chay: python3 main.py"
