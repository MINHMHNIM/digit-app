# Demo deploy: Nhận diện chữ số viết tay trên AWS EC2

Web app nhỏ: bạn vẽ một chữ số (0–9) trên trình duyệt, máy chủ chạy model AI và trả về chữ số đoán được kèm xác suất. Mục đích là **tập deploy một hệ thống AI lên máy ảo EC2** trong AWS Academy Learner Lab.

- **Backend:** FastAPI (Python)
- **Model:** SVM (scikit-learn), huấn luyện trên bộ `digits` có sẵn trong scikit-learn (không cần tải dataset)
- **Frontend:** 1 file HTML, vẽ bằng chuột hoặc ngón tay
- **Deploy:** Ubuntu trên EC2, app chạy nền bằng `systemd` ở cổng 80

Khi chạy trên EC2, chân trang web sẽ hiện instance ID, loại máy và vùng (Availability Zone). Đó là bằng chứng app đang chạy trên cloud chứ không phải máy bạn.

## Cấu trúc thư mục

```
digit-app/
├── app/
│   ├── main.py          # API: /, /health, /api/thong-tin, /api/du-doan
│   ├── model.py         # Huấn luyện và tải model
│   ├── xu_ly_anh.py     # Tiền xử lý nét vẽ thành ảnh 8x8
│   └── static/index.html
├── deploy/
│   ├── setup.sh         # Chạy 1 lần trên EC2 để cài và khởi động app
│   ├── cap-nhat.sh      # Chạy mỗi khi có code mới
│   └── digit-app.service
└── requirements.txt
```

## Luồng hoạt động

```
Trình duyệt ──(ảnh PNG nét vẽ)──► EC2: FastAPI ──► tiền xử lý → ảnh 8×8 ──► model SVM
     ▲                                                                         │
     └──────────────────(chữ số + xác suất 0–9 + ảnh 8×8)──────────────────────┘
```

---

## Bước 0 (tùy chọn): Chạy thử trên máy mình

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Mở `http://localhost:8000`. Chân trang sẽ báo "không phải EC2", như vậy là đúng.

## Bước 1: Đưa code lên GitHub

Tạo một repo **public** trên GitHub (ví dụ `digit-app`) rồi đẩy code lên:

```bash
git init
git add .
git commit -m "Demo nhan dien chu so"
git branch -M main
git remote add origin https://github.com/<ten-github-cua-ban>/digit-app.git
git push -u origin main
```

> Không quen dùng git thì có thể vào repo trên GitHub, chọn **Add file → Upload files** và kéo thả cả thư mục vào.

## Bước 2: Tạo máy ảo EC2

1. Vào AWS Academy, mở **Learner Lab**, bấm **Start Lab** và chờ chấm chuyển xanh. Sau đó bấm **AWS** để mở Console.
2. Gõ **EC2** vào ô tìm kiếm, chọn **Launch instance**.
3. Điền như sau:

| Mục | Chọn |
|---|---|
| Name | `digit-app` |
| Application and OS Images | **Ubuntu**, bản *Ubuntu Server 24.04 LTS* |
| Instance type | **t3.micro** |
| Key pair | **vockey** |
| Network settings | Tick **Allow SSH traffic from Anywhere** và **Allow HTTP traffic from the internet** |
| Storage | Giữ mặc định (8 GiB) |

4. Bấm **Launch instance**, rồi vào **View all instances** và chờ cột *Instance state* chuyển thành **Running**.

> Tick "Allow HTTP traffic" chính là mở **cổng 80** trong *Security Group* (tường lửa của máy). Thiếu bước này thì người ngoài không vào được web.

## Bước 3: Kết nối vào máy

Chọn instance, bấm **Connect**, chọn tab **EC2 Instance Connect**, rồi bấm **Connect**. Một cửa sổ terminal sẽ mở ngay trong trình duyệt, đăng nhập với user `ubuntu`.

> Nếu cách này lỗi, xem phần *Xử lý sự cố* để kết nối bằng SSH.

## Bước 4: Cài và chạy app

Trong terminal của EC2:

```bash
git clone https://github.com/<ten-github-cua-ban>/digit-app.git
cd digit-app
bash deploy/setup.sh
```

Script sẽ tự cài Python, thư viện, huấn luyện model (vài giây) và bật app. Cả quá trình mất khoảng 2–5 phút. Cuối cùng màn hình sẽ in ra:

```
Deploy xong! Mở trình duyệt và vào: http://54.xx.xx.xx
```

## Bước 5: Mở web

Mở địa chỉ vừa in ra, hoặc lấy **Public IPv4 address** ở trang chi tiết instance.

⚠️ Gõ rõ **`http://`** ở đầu. Nhiều trình duyệt tự đổi sang `https://`, mà app này chưa có HTTPS nên sẽ không vào được.

Gửi link cho bạn bè thử, ai có link cũng dùng được.

---

## Sửa code và deploy lại

Sửa code trên máy bạn, rồi `git push`. Sau đó trên EC2 chạy:

```bash
cd ~/digit-app
bash deploy/cap-nhat.sh
```

## Khi hết phiên lab 4 tiếng

- Hết phiên thì máy EC2 bị **stop**, web tạm thời không vào được.
- Lần sau bấm **Start Lab**. Nếu instance chưa tự chạy lại, vào EC2, chọn instance, rồi **Instance state → Start instance**.
- App **tự bật lại** khi máy khởi động (nhờ `systemd`), bạn không cần chạy lại script.
- **IP công khai thường bị đổi** sau mỗi lần stop/start, nên phải lấy IP mới ở trang EC2.

## Các lệnh hữu ích trên EC2

```bash
sudo systemctl status digit-app        # Xem app có đang chạy không
sudo journalctl -u digit-app -n 50     # Xem 50 dòng log gần nhất
sudo journalctl -u digit-app -f        # Xem log trực tiếp (Ctrl+C để thoát)
sudo systemctl restart digit-app       # Khởi động lại app
curl http://localhost/health           # Tự kiểm tra từ bên trong máy
```

## Chi phí

t3.micro khoảng 0.0104 USD/giờ, cộng IP công khai khoảng 0.005 USD/giờ, tổng **khoảng 0.015 USD/giờ**. Một phiên 4 tiếng tốn khoảng **0.06 USD**, rất nhỏ so với 100 USD credit. Khi máy đã stop thì chỉ còn tính phí ổ đĩa (rất ít).

Làm xong, không cần nữa thì **Terminate** instance (Instance state → Terminate) để dọn sạch.

## Xử lý sự cố

**Web không vào được (quay mãi rồi lỗi)**
1. Kiểm tra đã gõ `http://`, không phải `https://`.
2. Trên EC2, chạy `curl http://localhost/health`. Nếu ra `{"trang_thai":"ok"}` tức là app chạy tốt và lỗi nằm ở tường lửa. Vào instance, chọn tab **Security**, bấm vào Security group, chọn **Edit inbound rules** và thêm rule **HTTP, port 80, source 0.0.0.0/0**.
3. Nếu `curl` lỗi, xem log bằng `sudo journalctl -u digit-app -n 50`.

**EC2 Instance Connect không kết nối được, dùng SSH thay thế**
1. Trên trang Learner Lab, bấm **AWS Details**, rồi **Download PEM** để tải file `labsuser.pem`.
2. Trên máy bạn (macOS/Linux, hoặc PowerShell trên Windows):
   ```bash
   chmod 400 labsuser.pem
   ssh -i labsuser.pem ubuntu@<IP-cong-khai>
   ```

**`pip install` bị "Killed"**
Máy thiếu RAM. Hãy stop instance, vào **Actions → Instance settings → Change instance type**, chọn **t3.small**, rồi start lại và chạy lại `bash deploy/setup.sh`.

---

## API

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/` | Giao diện vẽ |
| GET | `/health` | Kiểm tra app còn sống |
| GET | `/api/thong-tin` | Hostname, thông tin EC2, độ chính xác model |
| POST | `/api/du-doan` | Body `{"anh": "<ảnh PNG dạng base64>"}`, trả về `chu_so`, `xac_suat`, `anh_8x8` |
| GET | `/docs` | Trang tài liệu API tự sinh của FastAPI (thử API ngay trên trình duyệt) |

## Giới hạn của model

Model được huấn luyện trên ảnh chữ số 8×8 (bộ `digits` của scikit-learn) nên khá nhẹ, chạy tốt trên t3.micro. Đổi lại, model đôi khi đoán nhầm nét vẽ lạ, hay gặp nhất là các cặp 1/8, 6/8, 8/9. Độ chính xác trên tập test khoảng 99%. Thử với nét vẽ mô phỏng thì đúng khoảng 90%.

## Ý tưởng mở rộng

- Lưu mỗi ảnh người dùng vẽ lên **S3** để sau này huấn luyện lại model.
- Dùng **User data** khi tạo EC2 để máy tự `git clone` và chạy `setup.sh`, không cần SSH vào.
- Thay model này bằng model của đồ án thật: train trên Kaggle/Colab, đưa file weights lên, giữ nguyên phần FastAPI và deploy.
