import struct, os

MEMBERS_FILE = 'members.dat'
MEMBER_FORMAT = '< c i 64s 16s'  # is_active, member_id, name, phone
MEMBER_RECORD_SIZE = struct.calcsize(MEMBER_FORMAT)

STATUS_ACTIVE = b'A'
STATUS_DELETED = b'D'

def pack_string(s, length):
    """แปลง string เป็น bytes fixed length"""
    return s.encode('utf-8')[:length].ljust(length, b'\x00')

def unpack_string(b):
    """แปลง bytes เป็น string"""
    return b.rstrip(b'\x00').decode('utf-8')

def get_last_id(filename, record_size):
    """ดึง ID ล่าสุดในไฟล์ (return 0 ถ้าไฟล์ว่าง)"""
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return 0
    with open(filename, 'rb') as f:
        f.seek(-record_size, os.SEEK_END)
        record = f.read(record_size)
        return struct.unpack('<i', record[1:5])[0]

def add_member():
    last_id = get_last_id(MEMBERS_FILE, MEMBER_RECORD_SIZE)
    member_id = last_id + 1
    print(f"\n--- เพิ่มสมาชิก (ID: {member_id}) ---")
    name = input("ชื่อ-สกุล: ")
    phone = input("เบอร์โทร: ")
    record = struct.pack(MEMBER_FORMAT, STATUS_ACTIVE, member_id, pack_string(name,64), pack_string(phone,16))
    with open(MEMBERS_FILE,'ab') as f:
        f.write(record)
    print(f"✅ เพิ่มสมาชิก '{name}' เรียบร้อยแล้ว")

def view_all_members():
    if not os.path.exists(MEMBERS_FILE) or os.path.getsize(MEMBERS_FILE)==0:
        print("ยังไม่มีข้อมูลสมาชิก")
        return
    print("\n--- 👥 รายการสมาชิก ---")
    with open(MEMBERS_FILE, 'rb') as f:
        while True:
            record = f.read(MEMBER_RECORD_SIZE)
            if not record: break
            status, member_id, name, phone = struct.unpack(MEMBER_FORMAT, record)
            if status == STATUS_ACTIVE:
                print(f"ID:{member_id}, Name:{unpack_string(name)}, Phone:{unpack_string(phone)}")

def update_member():
    member_id = int(input("ID สมาชิกที่ต้องการแก้ไข: "))
    if not os.path.exists(MEMBERS_FILE) or os.path.getsize(MEMBERS_FILE)==0:
        print("ยังไม่มีข้อมูลสมาชิก")
        return
    with open(MEMBERS_FILE, 'r+b') as f:
        while True:
            pos = f.tell()
            record = f.read(MEMBER_RECORD_SIZE)
            if not record: break
            r_status, r_id, old_name, old_phone = struct.unpack(MEMBER_FORMAT, record)
            if r_status == STATUS_ACTIVE and r_id == member_id:
                print("แก้ไข (เว้นว่าง = ไม่เปลี่ยน)")
                name = input(f"ชื่อ-สกุล ({unpack_string(old_name)}): ") or unpack_string(old_name)
                phone = input(f"เบอร์โทร ({unpack_string(old_phone)}): ") or unpack_string(old_phone)
                new_record = struct.pack(MEMBER_FORMAT, STATUS_ACTIVE, member_id, pack_string(name,64), pack_string(phone,16))
                f.seek(pos)
                f.write(new_record)
                print("✅ อัปเดตสมาชิกเรียบร้อย")
                return
    print("ไม่พบสมาชิก")

def delete_member():
    member_id = int(input("ID สมาชิกที่ต้องการลบ: "))
    if not os.path.exists(MEMBERS_FILE) or os.path.getsize(MEMBERS_FILE)==0:
        print("ยังไม่มีข้อมูลสมาชิก")
        return
    with open(MEMBERS_FILE, 'r+b') as f:
        while True:
            pos = f.tell()
            record = f.read(MEMBER_RECORD_SIZE)
            if not record: break
            r_status, r_id, name, phone = struct.unpack(MEMBER_FORMAT, record)
            if r_status == STATUS_ACTIVE and r_id == member_id:
                confirm = input(f"ลบสมาชิก '{unpack_string(name)}'? (y/n): ")
                if confirm.lower() == 'y':
                    deleted_record = struct.pack(MEMBER_FORMAT, STATUS_DELETED, r_id, name, phone)
                    f.seek(pos)
                    f.write(deleted_record)
                    print("✅ ลบสมาชิกเรียบร้อย")
                return
    print("ไม่พบสมาชิก")

def members_menu():
    while True:
        print("\n--- 👤 เมนูสมาชิก ---")
        print("1. เพิ่มสมาชิก")
        print("2. แสดงสมาชิกทั้งหมด")
        print("3. แก้ไขสมาชิก")
        print("4. ลบสมาชิก")
        print("0. กลับ")
        ch = input("เลือก: ")
        if ch == '1': add_member()
        elif ch == '2': view_all_members()
        elif ch == '3': update_member()
        elif ch == '4': delete_member()
        elif ch == '0': break
        else: print("❌ โปรดเลือกตัวเลือกที่ถูกต้อง")
