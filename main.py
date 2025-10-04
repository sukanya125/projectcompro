import os
from books import books_menu
from members import members_menu
from lendings import lendings_menu
from report import generate_report

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("==============================")
        print("  PyLibMan - ระบบจัดการห้องสมุด")
        print("==============================")
        print("1. จัดการหนังสือ")
        print("2. จัดการสมาชิก")
        print("3. จัดการการยืม-คืน")
        print("4. สร้างรายงาน")
        print("0. ปิดโปรแกรม")
        
        choice = input("เลือกเมนูหลัก: ")
        
        if choice == '1':
            books_menu()
        elif choice == '2':
            members_menu()
        elif choice == '3':
            lendings_menu()
        elif choice == '4':
            generate_report()
            input("\nกด Enter เพื่อไปต่อ...")
        elif choice == '0':
            print("ปิดโปรแกรม")
            break
        else:
            print("ตัวเลือกไม่ถูกต้อง")
            input("กด Enter เพื่อไปต่อ...")

if __name__ == '__main__':
    main()
