# He thong kiem soat lop hoc - Raspberry Pi 4

Ban nay danh cho Raspberry Pi 4. App uu tien camera CSI qua `Picamera2`, neu khong co se fallback sang USB camera qua OpenCV.

## Cai dat tren Raspberry Pi

```bash
cd ~/doan_thuc_raspi
chmod +x install_raspi.sh
./install_raspi.sh
```

Kiem tra camera:

```bash
rpicam-hello --list-cameras
rpicam-hello --timeout 3000
```

Chay app:

```bash
python3 main.py
```

## Tai code tu GitHub

Sau khi repo duoc push len GitHub:

```bash
git clone <URL_REPO_GITHUB>
cd doan_thuc_raspi
chmod +x install_raspi.sh
./install_raspi.sh
python3 main.py
```

## Ghi chu

- Can chay trong moi truong desktop/VNC/RDP cua Raspberry Pi, vi app dung PyQt6.
- Neu dung SSH thuong khong co man hinh, hay mo app bang VNC Viewer hoac Remote Desktop.
- Neu camera CSI khong hien, thu `rpicam-hello --list-cameras` de kiem tra Pi da nhan camera chua.
