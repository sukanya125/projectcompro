import struct
import os
import datetime
from books import BOOKS_FILE, BOOK_FORMAT, BOOK_RECORD_SIZE, STATUS_ACTIVE, unpack_string
from members import MEMBERS_FILE, MEMBER_FORMAT, MEMBER_RECORD_SIZE, STATUS_ACTIVE as MEMBER_ACTIVE
from lendings import LENDINGS_FILE, LENDING_FORMAT, LENDING_RECORD_SIZE, STATUS_BORROWED, STATUS_RETURNED

def generate_report():
    lines = []
    lines.append("=" * 120)
    lines.append("Library Management System – Lending Report".center(120))
    lines.append(f"Generated At : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(120))
    lines.append("App Version : 1.0".center(120))
    lines.append("Encoding : UTF-8".center(120))
    lines.append("=" * 120)
    lines.append("")
    header = f"{'สมาชิก':<30} {'เบอร์โทร':<18} {'หนังสือ':<50} {'สถานะ':<12}"
    lines.append(header)
    lines.append("=" * 120)
    members_dict = {}
    if os.path.exists(MEMBERS_FILE) and os.path.getsize(MEMBERS_FILE) > 0:
        with open(MEMBERS_FILE, 'rb') as f:
            for _ in range(os.path.getsize(MEMBERS_FILE) // MEMBER_RECORD_SIZE):
                r = f.read(MEMBER_RECORD_SIZE)
                status, member_id, name, phone = struct.unpack(MEMBER_FORMAT, r)
                if status == MEMBER_ACTIVE:
                    members_dict[member_id] = {
                        'name': unpack_string(name),
                        'phone': unpack_string(phone)
                    }
    books_dict = {}
    if os.path.exists(BOOKS_FILE) and os.path.getsize(BOOKS_FILE) > 0:
        with open(BOOKS_FILE, 'rb') as f:
            for _ in range(os.path.getsize(BOOKS_FILE) // BOOK_RECORD_SIZE):
                r = f.read(BOOK_RECORD_SIZE)
                status, book_id, _, title, _, _ = struct.unpack(BOOK_FORMAT, r)
                if status == STATUS_ACTIVE:
                    books_dict[book_id] = unpack_string(title)
    total_lendings = borrowed_count = returned_count = 0
    member_lendings = {}  # key = member_name, value = dict {phone, books[], status_counts}

    if os.path.exists(LENDINGS_FILE) and os.path.getsize(LENDINGS_FILE) > 0:
        with open(LENDINGS_FILE, 'rb') as f:
            for _ in range(os.path.getsize(LENDINGS_FILE) // LENDING_RECORD_SIZE):
                r = f.read(LENDING_RECORD_SIZE)
                status, _, bid, mid, _, _ = struct.unpack(LENDING_FORMAT, r)
                total_lendings += 1
                if status == STATUS_BORROWED:
                    borrowed_count += 1
                elif status == STATUS_RETURNED:
                    returned_count += 1
                member_info = members_dict.get(mid, {'name': 'ไม่ระบุ', 'phone': '-'})
                member_name = member_info['name']
                member_phone = member_info['phone']
                if member_name not in member_lendings:
                    member_lendings[member_name] = {
                        'phone': member_phone,
                        'books': [],
                        'statuses': []
                    }
                member_lendings[member_name]['books'].append(books_dict.get(bid, "ไม่พบชื่อหนังสือ"))
                member_lendings[member_name]['statuses'].append(status)
    for member_name, data in member_lendings.items():
        book_titles = ", ".join(data['books'])
        # กำหนดสถานะ: ถ้ามีเล่มใดยังยืมอยู่ให้แสดง 📕 ยืมอยู่, ถ้าคืนหมดแล้วแสดง ✅ คืนแล้ว
        if STATUS_BORROWED in data['statuses']:
            status_text = "📕 ยืมอยู่"
        else:
            status_text = "✅ คืนแล้ว"

        lines.append(f"{member_name:<30} {data['phone']:<18} {book_titles:<50} {status_text:<12}")

    lines.append("=" * 120)
    lines.append("")
    lines.append("Summary".center(120))
    lines.append("-" * 120)
    lines.append(f"- Total Lendings     : {total_lendings}")
    lines.append(f"- Currently Borrowed : {borrowed_count}")
    lines.append(f"- Already Returned   : {returned_count}")
    lines.append("=" * 120)
    with open('library_report.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print("✅ สร้างรายงาน library_report.txt เรียบร้อยแล้ว")
