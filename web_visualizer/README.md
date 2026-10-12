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

1. `Tiền xử lý`: tách câu, chuẩn hóa, token hóa tiếng Việt, bỏ câu có tối đa 4 token. Mở từng câu để xem token.
2. `KMeans`: Word2Vec 256 chiều, cộng vector từ thành vector câu, gom cụm và chọn câu gần tâm. Mỗi thẻ hiển thị số thành viên thực tế, mở rộng để đọc các câu trong cụm.
3. `Centroid`: chấm điểm TF-IDF theo chủ đề chung và lọc câu quá giống nhau (ngưỡng 0,95). Thanh điểm và nhãn cho biết câu được giữ.
4. `MMR`: hiển thị thứ tự chọn thực tế, điểm liên quan và trùng lặp với công thức λ = 0,6. Câu đầu là câu mốc; chế độ train dùng mục tiêu số ứng viên Centroid trừ 4, tối thiểu giữ câu mốc.
5. `Vị trí & kết quả`: bổ sung câu theo vị trí đến độ dài mục tiêu, hiển thị nguồn và lý do chọn; tô vàng câu được chọn trong văn bản nguồn và hỗ trợ sao chép.

## Số câu và bố cục

- Để trống **Số câu tóm tắt** để dùng quy tắc trong `Kmeans_CentroidBase_MMR_SentencePosition.py`: dưới 20 câu hợp lệ → 3 cụm; 20–49 → 5; 50–99 → 8; từ 100 → 10. Số câu tự động tối đa bằng số câu đại diện và không vượt số câu đầu vào.
- Nhập số nguyên 1–16 để đặt độ dài mong muốn; đầu ra giới hạn theo số câu đại diện có sẵn.
- Kéo thanh có dấu ⋮ giữa hai vùng để đổi chiều rộng. Có thể dùng phím ←/→ khi thanh được focus; nhấp đúp để đặt lại. Chiều rộng được lưu trong trình duyệt. Màn hình nhỏ chuyển thành bố cục dọc.

## Ghi chú

- `.txt` được đọc trực tiếp với nhiều encoding phổ biến.
- `.docx` cần `python-docx`.
- `.pdf` cần `pypdf`; chất lượng trích xuất phụ thuộc vào PDF có text thật hay chỉ là ảnh scan.
- Điểm và cụm trong giao diện dùng để trực quan hóa pipeline, không ghi đè dữ liệu trong `Data/ViMs`.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m unittest web_visualizer.test_app -v
```
