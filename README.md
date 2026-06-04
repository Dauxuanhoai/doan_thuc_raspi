# He thong kiem soat lop hoc - Raspberry Pi 4

Ban nay danh cho Raspberry Pi 4. Ung dung chay bang PyQt6 tren man hinh HDMI hoac VNC, va uu tien camera CSI qua `Picamera2`. Neu khong co camera CSI, app fallback sang USB camera bang OpenCV.

## Cai dat tren Raspberry Pi

```bash
git clone https://github.com/Dauxuanhoai/doan_thuc_raspi.git
cd doan_thuc_raspi
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

## Ghi chu hien thi

- App can chay trong desktop cua Raspberry Pi, qua HDMI hoac VNC.
- Neu dang SSH thuong ma khong co desktop, hay mo bang VNC Viewer roi chay terminal trong desktop.
- Neu ban dung LCD 3.5 inch rieng o `/dev/fb1`, app nay van nen chay tren HDMI/VNC. LCD phu co the duoc dieu khien bang code rieng.

## Du lieu sinh ra khi chay

Cac thu muc/file sau duoc bo qua trong git:

- `classroom.db`
- `photos/`
- `face_data/`
- `exports/`
- `__pycache__/`

## Loi camera thuong gap

- Camera CSI khong hien: chay `rpicam-hello --list-cameras` de kiem tra Pi da nhan camera chua.
- USB camera bi chiem: dong app khac dang dung camera roi chay lai.
- Khong mo duoc giao dien: dam bao dang o HDMI/VNC desktop, khong phai SSH headless.
