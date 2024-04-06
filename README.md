# **About Project**
**Dự Án Quản Lý Hoạt Động Tình Nguyện (Volunteer Management)** là đề tài cuối kỳ của môn Công Nghệ Mới Trong Phát Triển Ứng Dụng. Trong dự án này, chúng tôi sẽ phát triển một ứng dụng web bằng Django, nhằm hỗ trợ tổ chức tình nguyện trong việc quản lý và theo dõi các hoạt động tình nguyện.

<details>
   <summary><strong>👇Hướng dẫn và các lệnh làm việc với Django</strong></summary>

# **Django commands and tips for development**

## I.Tạo project mới:
Mở terminal và di chuyển đến thư mục mà bạn muốn tạo project mới. Sau đó chạy lệnh sau:

### 1. Tạo môi trưởng ảo: 
Tạo môi trường ảo với tên là `py3.12_venv` tại thư mục của project
```bash
python -m venv py3.12_venv
```
### 2. Kích hoạt môi trường ảo:
```bash
py3.12_venv\Scripts\activate 
```
### 3. Cài đặt Django:
```bash
pip install django
```
### 4. Tạo project mới:
Tạo project Django mới với tên là `volunteer_management` tại thư mục hiện tại
```bash
django-admin startproject volunteer_management
```

### 5. Tạo app mới:
Tạo app mới với tên là `volunteer_app` tại thư mục hiện tại
```bash
cd volunteer_management
```
```bash
python manage.py startapp volunteer_app
```

- Để thêm app mới vào project, mở file `volunteer_management/settings.py` và thêm tên app vào `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'volunteer_management_app',
    ...
]
```

### 6. Chạy thử server:
```bash
python manage.py runserver
```
- Mở trình duyệt và truy cập vào địa chỉ [http://127.0.0.1:8000/](http://127.0.0.1:8000/), nếu bạn thấy trang web như hình dưới đây thì đã cài đặt thành công:
![alt text](README_images/image.png)

## II. Các lệnh thường dùng để làm việc với Django:

### Kích hoạt môi trường ảo trước khi làm việc:
```bash
py3.12_venv\Scripts\activate 
```

### 1. Tạo database:
```bash
python manage.py makemigrations volunteer_app
```

### 2. Migrate database:
```bash
python manage.py migrate
```

### 3. Tạo superuser:
```bash
python manage.py createsuperuser
```

### 4. Chạy server:
```bash
python manage.py runserver
```
### 5. Chạy test case:
```bash
python manage.py test volunteer_app
```

### 6. Mở shell:
```bash
python manage.py shell
```

### 7. Tạo file requirements.txt:
```bash
pip freeze > requirements.txt
```
</details>




