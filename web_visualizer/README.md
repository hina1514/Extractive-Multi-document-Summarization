# Web trực quan hóa tóm tắt đa văn bản

Web local này cho phép nhập nhiều văn bản, thêm ô nhập, upload file `.txt`, `.docx`, `.pdf`, chạy từng bước và xem câu nào trong văn bản gốc được chọn vào bản tóm tắt.

## Cài thư viện

Từ folder gốc của repo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\web_visualizer\requirements.txt
```

## Chạy web

```powershell
.\.venv\Scripts\python.exe .\web_visualizer\app.py
```

Mở trình duyệt tại:

```text
http://127.0.0.1:5000
```

## Các bước trên web

1. `Tiền xử lý`: tách câu, token hóa tiếng Việt, bỏ câu quá ngắn.
2. `KMeans`: vector hóa TF-IDF, gom cụm câu, chọn câu gần centroid nhất của mỗi cụm.
3. `MMR`: chọn câu quan trọng nhưng giảm trùng lặp giữa các câu.
4. `Output`: hiển thị bản tóm tắt và highlight lại các câu được chọn trong văn bản gốc.

## Ghi chú

- `.txt` được đọc trực tiếp với nhiều encoding phổ biến.
- `.docx` cần `python-docx`.
- `.pdf` cần `pypdf`; chất lượng trích xuất phụ thuộc vào PDF có text thật hay chỉ là ảnh scan.
- Điểm và cụm trong giao diện dùng để trực quan hóa pipeline, không ghi đè dữ liệu trong `Data/ViMs`.
