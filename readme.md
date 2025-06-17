python3 -m virtualenv venv --python=3.9
venv\Scripts\activate.bat

- Cài đặt wheel ldap 3.4.4:
pip install python_ldap-3.4.4-cp39-cp39-win_amd64.whl
- Cài đặt các requirement khác:
pip install -r requirements.txt

**Chạy test**
python simulation.py --t 0 [--t] [--n] [--rt] [--amin] [--amax] [--bmin] [--bmax] [--gmin] [--gmax]

- (--t): Loại thực nghiệm. Trong đó:
    + 0: Chạy test t100 1 lần
    + 1: Chạy test --n, --rt lần
    + 2: Chạy test --n, --rt lần, với điều kiện --a và --g
    + 3: Chạy test --n, --rt lần, với điều kiện --a, --b, --g
- (--n): Tên test trong thư mục data (không có yaml)
- (--rt): Số lần chạy
- (--_min) , (--_max): Giá trị nhỏ nhất và lớn nhất của tham số khi khởi chạy