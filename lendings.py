import struct, os, time, datetime
from books import BOOKS_FILE, BOOK_FORMAT, BOOK_RECORD_SIZE, STATUS_ACTIVE, unpack_string, pack_string
from members import MEMBERS_FILE, MEMBER_FORMAT, MEMBER_RECORD_SIZE

# ============================================
# กำหนดค่าคอนฟิกสำหรับไฟล์การยืม-คืน
# ============================================
LENDINGS_FILE = 'lendings.dat'  # ชื่อไฟล์ binary สำหรับเก็บข้อมูลการยืม-คืน
LENDING_FORMAT = '< c i i i d d'  # โครงสร้างข้อมูล: สถานะ(1 byte), lending_id(4), book_id(4), member_id(4), วันยืม(8), วันคืน(8)
LENDING_RECORD_SIZE = struct.calcsize(LENDING_FORMAT)  # คำนวณขนาดของแต่ละ record (29 bytes)
STATUS_BORROWED = b'A'  # สถานะ 'A' = Active (กำลังยืมอยู่)
STATUS_RETURNED = b'R'  # สถานะ 'R' = Returned (คืนแล้ว)

# ============================================
# ฟังก์ชันช่วยเหลือ: หา ID ล่าสุดในไฟล์
# ============================================
def get_last_id(filename, record_size):
    """
    อ่าน record สุดท้ายในไฟล์เพื่อดึง ID ล่าสุด
    ใช้สำหรับสร้าง ID ใหม่ (ID_ล่าสุด + 1)
    """
    # ตรวจสอบว่าไฟล์มีอยู่และไม่ว่างเปล่า
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return 0  # ถ้าไม่มีไฟล์หรือว่างเปล่า ส่งค่า 0
    
    with open(filename, 'rb') as f:
        f.seek(-record_size, os.SEEK_END)  # ไปที่ record สุดท้าย (นับจากท้ายไฟล์)
        record = f.read(record_size)  # อ่าน record สุดท้าย
        return struct.unpack('<i', record[1:5])[0]  # ดึงค่า ID จากตำแหน่ง byte 1-5

# ============================================
# ฟังก์ชันหลัก: ยืมหนังสือ
# ============================================
def borrow_book():
    book_id = int(input("Book ID ที่จะยืม: "))
    member_id = int(input("Member ID: "))
    book_found = False
    with open(BOOKS_FILE, 'rb') as bf:
        while True:
            r = bf.read(BOOK_RECORD_SIZE)  # อ่านทีละ record
            if not r:  # ถ้าอ่านจนหมดไฟล์แล้ว
                break
            status, bid, _, title, _, qty = struct.unpack(BOOK_FORMAT, r)
            if status == STATUS_ACTIVE and bid == book_id:
                book_found = True
                book_title = unpack_string(title)  # แปลง bytes เป็น string
                book_qty = qty  # เก็บจำนวนคงเหลือ
                break
    if not book_found:
        print("❌ ไม่พบหนังสือ")
        return  # ออกจากฟังก์ชันทันที
    member_found = False
    with open(MEMBERS_FILE, 'rb') as mf:
        while True:
            r = mf.read(MEMBER_RECORD_SIZE)  # อ่านทีละ record
            if not r:
                break
            status, mid, name, _ = struct.unpack(MEMBER_FORMAT, r)
            if status == STATUS_ACTIVE and mid == member_id:
                member_found = True
                member_name = unpack_string(name)  # แปลง bytes เป็น string
                break
    if not member_found:
        print("❌ ไม่พบสมาชิก")
        return
    if book_qty <= 0:
        print("❌ หนังสือหมดสต็อก")
        return
    lending_id = get_last_id(LENDINGS_FILE, LENDING_RECORD_SIZE) + 1  # สร้าง ID ใหม่
    borrow_date = time.time()  # เก็บเวลาปัจจุบันเป็น timestamp
    return_date = 0.0  # ยังไม่ได้คืน ใส่ 0
    record = struct.pack(LENDING_FORMAT, STATUS_BORROWED, lending_id, book_id, member_id, borrow_date, return_date)
    with open(LENDINGS_FILE, 'ab') as f:
        f.write(record)
    with open(BOOKS_FILE, 'r+b') as bf:  # เปิดแบบ read+write
        while True:
            pos = bf.tell()  # จำตำแหน่งปัจจุบัน
            r = bf.read(BOOK_RECORD_SIZE)
            if not r:
                break
            status, bid, isbn, title, author, qty = struct.unpack(BOOK_FORMAT, r)
            if status == STATUS_ACTIVE and bid == book_id:
                qty -= 1  # ลดจำนวน 1
                new_record = struct.pack(BOOK_FORMAT, status, bid, isbn, title, author, qty)
                bf.seek(pos)  # กลับไปที่ตำแหน่งเดิม
                bf.write(new_record)  # เขียนทับ
                break
    print(f"✅ ยืมหนังสือ '{book_title}' สำเร็จโดย {member_name}")

# ============================================
# ฟังก์ชันหลัก: คืนหนังสือ
# ============================================
def return_book():
    """
    ฟังก์ชันสำหรับการคืนหนังสือ
    ขั้นตอน: ค้นหา Lending ID -> คำนวณค่าปรับ -> อัปเดตสถานะ -> เพิ่มสต็อกหนังสือ
    """
    lending_id = int(input("Lending ID คืน: "))
    found = False
    with open(LENDINGS_FILE, 'r+b') as f:
        while True:
            pos = f.tell()  # จำตำแหน่งปัจจุบัน
            r = f.read(LENDING_RECORD_SIZE)
            if not r:
                break
            status, lid, bid, mid, borrow_date, return_date = struct.unpack(LENDING_FORMAT, r)
            if status == STATUS_BORROWED and lid == lending_id:
                found = True
                return_time = time.time()  # เวลาคืนปัจจุบัน
                days = (return_time - borrow_date) / 86400  # แปลง seconds เป็นวัน (86400 = จำนวน seconds ใน 1 วัน)
                fine = max(0, int(days - 7) * 5)  # คำนวณค่าปรับ (ถ้าเกิน 7 วัน)
                new_record = struct.pack(LENDING_FORMAT, STATUS_RETURNED, lid, bid, mid, borrow_date, return_time)
                f.seek(pos)  # กลับไปที่ตำแหน่งเดิม
                f.write(new_record)  # เขียนทับ
                with open(BOOKS_FILE, 'r+b') as bf:
                    while True:
                        pos2 = bf.tell()
                        r2 = bf.read(BOOK_RECORD_SIZE)
                        if not r2:
                            break
                        status_b, bid_b, isbn, title, author, qty = struct.unpack(BOOK_FORMAT, r2)
                        if status_b == STATUS_ACTIVE and bid_b == bid:
                            qty += 1  # เพิ่มจำนวน 1
                            new_record_b = struct.pack(BOOK_FORMAT, status_b, bid_b, isbn, title, author, qty)
                            bf.seek(pos2)  # กลับไปตำแหน่งเดิม
                            bf.write(new_record_b)  # เขียนทับ
                            break
                print(f"✅ คืนสำเร็จ ค่าปรับ: {fine} บาท" if fine > 0 else "✅ คืนสำเร็จ ไม่มีค่าปรับ")
                break
    if not found:
        print("❌ ไม่พบ Lending ID")

# ============================================
# ฟังก์ชันแสดงข้อมูล: ดูประวัติการยืม-คืนทั้งหมด
# ============================================
def view_lendings():
    """
    แสดงรายการประวัติการยืม-คืนหนังสือทั้งหมด
    """
    # ตรวจสอบว่ามีไฟล์หรือไม่
    if not os.path.exists(LENDINGS_FILE):
        print("ยังไม่มีข้อมูลการยืม-คืน")
        return

    print("\n--- 📖 ประวัติยืม-คืน ---")
    with open(LENDINGS_FILE, 'rb') as f:
        while True:
            r = f.read(LENDING_RECORD_SIZE)
            if not r:
                break
            # แตก record
            status, lid, bid, mid, borrow_date, return_date = struct.unpack(LENDING_FORMAT, r)
            # แสดงเฉพาะรายการที่ Active (ยืมอยู่หรือคืนแล้ว)
            if status in [STATUS_BORROWED, STATUS_RETURNED]:
                # แปลง timestamp เป็นวันที่
                bdate = datetime.datetime.fromtimestamp(borrow_date).strftime("%Y-%m-%d")
                # ถ้ายังไม่คืน (return_date = 0) ให้แสดง "ยังไม่คืน"
                rdate = "ยังไม่คืน" if return_date == 0.0 else datetime.datetime.fromtimestamp(return_date).strftime("%Y-%m-%d")
                # กำหนดข้อความสถานะ
                status_text = "📕 ยืมอยู่" if status == STATUS_BORROWED else "✅ คืนแล้ว"
                # แสดงข้อมูล
                print(f"LID:{lid}, BookID:{bid}, MemberID:{mid}, ยืม:{bdate}, คืน:{rdate}, สถานะ:{status_text}")

# ============================================
# เมนูหลักสำหรับจัดการการยืม-คืน
# ============================================
def lendings_menu():
    """
    แสดงเมนูและรอรับคำสั่งจากผู้ใช้
    """
    while True:
        print("\n--- 📚 เมนูยืม-คืน ---")
        print("1. ยืมหนังสือ")
        print("2. คืนหนังสือ")
        print("3. ดูประวัติทั้งหมด")
        print("0. กลับ")
        ch = input("เลือก: ")
        
        # เรียกใช้ฟังก์ชันตามตัวเลือก
        if ch == '1':
            borrow_book()  # เรียกฟังก์ชันยืมหนังสือ
        elif ch == '2':
            return_book()  # เรียกฟังก์ชันคืนหนังสือ
        elif ch == '3':
            view_lendings()  # เรียกฟังก์ชันแสดงประวัติ
        elif ch == '0':
            break  # ออกจาก loop กลับไปเมนูหลัก