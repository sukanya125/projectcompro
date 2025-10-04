import struct, os

BOOKS_FILE = 'books.dat'
BOOK_FORMAT = '< c i 16s 128s 64s h'
# < = little-endian (วิธีเรียงไบต์แบบมาตรฐานของ Intel/AMD)
# c = char (1 byte) สำหรับเก็บสถานะ A หรือ D
# i = integer (4 bytes) สำหรับเก็บ ID
# 16s = string (16 bytes) สำหรับเก็บ ISBN
# 128s = string (128 bytes) สำหรับเก็บชื่อหนังสือ
# 64s = string (64 bytes) สำหรับเก็บชื่อผู้แต่ง
# h = short integer (2 bytes) สำหรับเก็บจำนวนเล่ม
BOOK_RECORD_SIZE = struct.calcsize(BOOK_FORMAT)

STATUS_ACTIVE = b'A'
STATUS_DELETED = b'D'

# ส่วนที่ 2: ฟังก์ชันช่วย (Helper Functions)
def pack_string(s, length): return s.encode('utf-8')[:length].ljust(length, b'\x00')
def unpack_string(b): return b.strip(b'\x00').decode('utf-8')

def get_last_id(filename, record_size):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0: return 0
    with open(filename, 'rb') as f:
        f.seek(-record_size, os.SEEK_END)
        record = f.read(record_size)
        return struct.unpack('<i', record[1:5])[0]


def add_book():
    last_id = get_last_id(BOOKS_FILE, BOOK_RECORD_SIZE)
    book_id = last_id + 1
    # --- ขั้นตอนที่ 1: สร้าง ID ใหม่ ---
    print(f"\n--- เพิ่มหนังสือ (ID: {book_id}) ---")
    # --- ขั้นตอนที่ 2: รับข้อมูลจากผู้ใช้ ---
    isbn = input("รหัสหนังสือ: ")
    title = input("ชื่อหนังสือ: ")
    author = input("ผู้แต่ง: ")
    quantity = int(input("จำนวนเล่ม: "))
    # --- ขั้นตอนที่ 3: Pack ข้อมูลเป็นไบนารี ---
    record = struct.pack(BOOK_FORMAT, STATUS_ACTIVE, book_id,
                         pack_string(isbn,16), pack_string(title,128),
                         pack_string(author,64), quantity)
    with open(BOOKS_FILE,'ab') as f: f.write(record)
    print(f"✅ เพิ่มหนังสือ '{title}' เรียบร้อยแล้ว")

def view_all_books():
    if not os.path.exists(BOOKS_FILE):
        print("ยังไม่มีข้อมูลหนังสือ"); return
    print("\n--- 📚 รายการหนังสือ ---")
    with open(BOOKS_FILE,'rb') as f:
        while True:
            record = f.read(BOOK_RECORD_SIZE)
            if not record: break
            status, book_id, isbn, title, author, qty = struct.unpack(BOOK_FORMAT, record)
            if status == STATUS_ACTIVE:
                print(f"ID:{book_id}, Title:{unpack_string(title)}, Author:{unpack_string(author)}, Qty:{qty}")

def update_book():
    book_id = int(input("ID หนังสือที่ต้องการแก้ไข: "))
    with open(BOOKS_FILE,'r+b') as f:
        while True:
            pos = f.tell()
            record = f.read(BOOK_RECORD_SIZE)
            if not record: break
            r_status,r_id,old_isbn,old_title,old_author,old_qty = struct.unpack(BOOK_FORMAT,record)
            if r_status==STATUS_ACTIVE and r_id==book_id:
                print("แก้ไข (เว้นว่าง = ไม่เปลี่ยน)")
                isbn = input(f"รหัสหนังสือ ({unpack_string(old_isbn)}): ") or unpack_string(old_isbn)
                title = input(f"ชื่อ ({unpack_string(old_title)}): ") or unpack_string(old_title)
                author= input(f"ผู้แต่ง ({unpack_string(old_author)}): ") or unpack_string(old_author)
                qty_s= input(f"จำนวน ({old_qty}): ")
                qty = int(qty_s) if qty_s else old_qty
                new_record = struct.pack(BOOK_FORMAT, STATUS_ACTIVE, book_id,
                                         pack_string(isbn,16), pack_string(title,128),
                                         pack_string(author,64), qty)
                f.seek(pos); f.write(new_record)
                print("✅ อัปเดตแล้ว"); return
    print("ไม่พบหนังสือ")

def delete_book():
    book_id = int(input("ID หนังสือที่ต้องการลบ: "))
    with open(BOOKS_FILE,'r+b') as f:
        while True:
            pos = f.tell() # บันทึกตำแหน่ง
            record = f.read(BOOK_RECORD_SIZE)
            if not record: break
            # Unpack ข้อมูลทั้งหมด (เพราะต้องเขียนกลับไปทั้งหมด)
            r_status,r_id,isbn,title,author,qty = struct.unpack(BOOK_FORMAT,record)
            if r_status==STATUS_ACTIVE and r_id==book_id:
                confirm=input(f"ลบ '{unpack_string(title)}'? (y/n): ")
                if confirm.lower()=='y':
                    deleted_record = struct.pack(BOOK_FORMAT, STATUS_DELETED,r_id,isbn,title,author,qty)
                    f.seek(pos); f.write(deleted_record)
                    print("✅ ลบแล้ว"); return
                else: return
    print("ไม่พบหนังสือ")

def books_menu():
    while True:
        print("\n--- 📖 เมนูหนังสือ ---")
        print("1. เพิ่มหนังสือ")
        print("2. แสดงทั้งหมด")
        print("3. แก้ไข")
        print("4. ลบ")
        print("0. กลับ")
        ch=input("เลือก: ")
        if ch=='1': add_book()
        elif ch=='2': view_all_books()
        elif ch=='3': update_book()
        elif ch=='4': delete_book()
        elif ch=='0': break
