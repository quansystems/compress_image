# Bài thực hành số 8 — Mô phỏng nén ảnh xám

Các file bám theo ba câu trong `Đề bài.pdf`:

- `cau1_chia_khoi.py`: hàm `split_blocks`, hiển thị ảnh, lưới khối, in khối mẫu và thử đệm ảnh cắt 13×19 thành 16×24.
- `cau2_dct.py`: hàm `dct_blocks`, in DC/AC, vẽ độ lớn `log(1 + |DCT|)` kèm thang màu.
- `cau3_luong_tu_hoa.py`: hàm `quantize`, thử ba mức 0.5, 1.0, 3.0 bằng bộ mã hóa/giải mã của đề; lưu ảnh, bảng CSV, ma trận và nhận xét. Thử cả ảnh đầy đủ và ảnh cắt 13×19.
- `jpeg_support.py`: code phần A được chép từ đề, nối lại các dòng bị ngắt trong PDF, giữ nguyên thuật toán.

## Chạy

Mở terminal tại thư mục `code` và cài thư viện:

```powershell
python -m pip install -r requirements.txt
```

Ảnh **RaceHorses_416x240_frame001.png** đã có trong thư mục `code`. Chạy từng câu:

```powershell
python cau1_chia_khoi.py
python cau2_dct.py
python cau3_luong_tu_hoa.py
```

Hoặc truyền đường dẫn ảnh xám/ảnh màu khác (chương trình tự đọc ở chế độ xám):

```powershell
python cau3_luong_tu_hoa.py "C:\duong_dan\anh.png" --no-show
```

Các câu 1 và 3 cần ảnh ít nhất 13×19 để thực hiện phép cắt theo đề. Mặc định kết quả được lưu ở `code/ket_qua/cau1`, `cau2`, `cau3`. Dùng `--output "thu_muc"` để đổi nơi lưu; dùng `--no-show` để chỉ lưu hình mà không mở cửa sổ. Khối mẫu của cả ba câu là khối số 0 ở góc trên trái.

Trong CSV, `ti_le_he_so_0` là số trong [0, 1]; nhân 100 để lấy phần trăm. Số bit chỉ là độ dài chuỗi Huffman, không phải dung lượng file JPEG. Các PNG dựng lại được lưu để quan sát, không phải file JPEG của bộ mô phỏng.
