# Bài thực hành số 8 – Mô phỏng nén ảnh xám

**Nguyễn Văn Quân – MSV 23020761** · Xử lí ảnh và thị giác

Chia ảnh thành khối 8×8, biến đổi DCT và lượng tử hóa; ghép với mã hỗ trợ Zigzag/RLE/Huffman trong đề bài để dựng lại ảnh.

- [Báo cáo PDF](bao_cao/23020761_NguyenVanQuan.pdf)
- [Báo cáo Word có thể chỉnh sửa](bao_cao/23020761_NguyenVanQuan.docx)
- [Đề bài](code/Đề%20bài.pdf)
- [Hướng dẫn mã nguồn](code/README.md)
- [Kết quả kiểm tra](bao_cao/kiem_tra.json)

## Chạy thực nghiệm

Yêu cầu Python 3.11 hoặc môi trường tương thích. Từ thư mục gốc:

```powershell
python -m pip install -r code/requirements.txt
python code/cau1_chia_khoi.py --no-show
python code/cau2_dct.py --no-show
python code/cau3_luong_tu_hoa.py --no-show
python verify_results.py
```

Ảnh RaceHorses đã có trong `code/`. Kết quả hình, ma trận và bảng CSV nằm trong `code/ket_qua/`.

## Tạo lại báo cáo

```powershell
python -m pip install -r requirements-report.txt
python build_report.py
```

Script tạo cả PDF và DOCX từ mã nguồn và kết quả thực nghiệm hiện có. Script sử dụng phông Times New Roman/Consolas trong `C:/Windows/Fonts`; nếu chạy trên hệ điều hành khác, cần sửa đường dẫn và tên phông tương ứng. Logo và thông tin bìa lấy từ mẫu báo cáo có sẵn trong `BaoCaoTemplate/`.

## Kết quả ảnh đầy đủ (240 × 416)

| Scale | MSE | Bit dữ liệu | Hệ số bằng 0 |
|---|---:|---:|---:|
| 0.5 | 12.34 | 166,471 | 70.8% |
| 1.0 | 30.47 | 108,113 | 81.1% |
| 3.0 | 97.46 | 47,347 | 91.9% |

Số bit chỉ tính chuỗi Huffman, chưa gồm bảng mã, Q và metadata; đây là mô phỏng, không phải dung lượng file JPEG chuẩn. MSE của ảnh cần đệm được tính sau khi cắt về kích thước ban đầu.
