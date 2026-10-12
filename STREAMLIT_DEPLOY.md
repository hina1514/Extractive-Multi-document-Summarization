# Chạy và triển khai trên Streamlit

Entry point: `streamlit_app.py`. Bản Streamlit giữ giao diện web, hai chế độ,
tham số λ, tải nhiều file, thanh chia vùng, các cảnh demo và Sort cuối.
Không cần chạy server Flask riêng hoặc mở cổng 5000/8765.

## Chạy local

Dùng Python **3.13** để khớp bộ thư viện đã kiểm tra:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m streamlit run streamlit_app.py
```

Mở `http://localhost:8501`. Nếu môi trường ảo đã có thì bỏ qua lệnh tạo môi trường.
Nếu Python của môi trường ảo đã bị gỡ/đổi đường dẫn, tạo lại môi trường trước khi cài.

## Streamlit Community Cloud

1. Đưa các thay đổi lên repository `hina1514/Extractive-Multi-document-Summarization` trên GitHub.
2. Đăng nhập [Streamlit Community Cloud](https://share.streamlit.io/) và liên kết tài khoản GitHub.
3. Chọn **Create app**, repository ở trên và nhánh **`codex/deploy-streamlit`**.
4. **Main file path:** `streamlit_app.py` (nằm ở thư mục gốc).
5. Trong **Advanced settings**, chọn Python **3.13**, rồi **Deploy**.

**Phải chọn Python 3.13 trước khi Deploy.** Phiên bản Python của app trên
Community Cloud được chọn trong giao diện Cloud, không được thay đổi bằng
`requirements.txt` hoặc thao tác Reboot.

Cloud cài thư viện từ `requirements.txt` ở thư mục gốc. `.streamlit/config.toml`
cấu hình giao diện và giới hạn file; không có secret cần nhập cho thuật toán này.
Không cần upload `.venv`, dataset `Data/ViMs`, file đánh giá ROUGE hoặc ảnh chụp giao diện.

Sau khi deploy thành công, Cloud cung cấp địa chỉ `https://<tên-app>.streamlit.app`.
Tài liệu chính thức: [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Giới hạn và cấu trúc

- Tổng file mỗi lần chạy tối đa **10 MB**; văn bản nhập tối đa **100.000 ký tự**.
- Giới hạn riêng của demo vẫn là 30 tài liệu và 5–300 câu hợp lệ.
- Các kết quả nằm trong session của từng người dùng; không dùng cache chung cho tài liệu.
- `web_visualizer/streamlit_bridge.py` chuyển dữ liệu sang các handler hiện có bằng Flask test client trong cùng tiến trình.
- Custom Component v2 chuyển yêu cầu và kết quả giữa giao diện và Streamlit; không gửi HTTP đến localhost của máy người xem.
- Phiên bản các thư viện được cố định để giữ trace K-means tương thích.

## Sửa lỗi `Failed to build gensim` trên Python 3.14

Nếu log ghi `Using Python 3.14.x` và `Failed to build gensim==4.4.0`, nguyên nhân
là Gensim 4.4.0 không có Linux wheel cho CPython 3.14. Cloud chuyển sang biên dịch
mã C, rồi lỗi do C API của Python 3.14. Gensim có Linux wheel cho Python 3.13.

1. Ghi lại subdomain, repository, branch, entry point và secrets (nếu đã nhập).
2. Xóa **app bị lỗi trên Streamlit Cloud**, không xóa repository GitHub.
3. Tạo app lại với repository và branch `codex/deploy-streamlit`, file `streamlit_app.py`.
4. Mở **Advanced settings → Python version → 3.13 → Save**, sau đó **Deploy**.
5. Xác nhận log mới ghi `Using Python 3.13.x` và tải file Gensim dạng `cp313...manylinux...whl`.

Root requirements sử dụng `--only-binary=gensim` để tránh biên dịch nhầm phiên bản.
Nếu vẫn chọn Python 3.14, tùy chọn này sẽ báo không có bản phù hợp; nó không tự
đổi Python của app. Chỉ reboot/push code không thay đổi Python đã chọn trên Cloud.

Hướng dẫn chính thức: [Đổi phiên bản Python trên Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python).

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest web_visualizer.test_app web_visualizer.test_pipeline_demo web_visualizer.test_source_order web_visualizer.test_streamlit_bridge -v
```
