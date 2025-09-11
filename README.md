# UP-Sports (UP-SFMS)

<<<<<<< Updated upstream
**University of Phayao - Sports Facility Management System**
=======
**โปรเจครายวิชา Fundamental of Database System และ Software Process โดยกลุ่ม *No Name !***  
สาขาวิศวกรรมซอฟต์แวร์ มหาวิท-ยาลัยพะเยา ปีการศึกษา 2568**
>>>>>>> Stashed changes

โปรเจครายวิชา _Fundamental of Database System_ และ _Software Process_  
โดยกลุ่ม **No Name !**  
สาขาวิศวกรรมซอฟต์แวร์ มหาวิทยาลัยพะเยา ปีการศึกษา 2568

---

## Project Overview

ระบบจัดการและวิเคราะห์ข้อมูลการใช้บริการสนามกีฬาและอุปกรณ์ โดยใช้ **QR Code** สำหรับเช็คอิน–เช็คเอาต์ผู้ใช้งาน  
มีเมนูแยก **Staff / User** และหน้า **Report** แสดงผลข้อมูลแบบ **สถิติ กราฟ และ Dashboard**

_A Django-based system for sports facility management, providing QR-based check-in/out,  
equipment usage tracking, role-based menus, and reporting dashboards._

---

## Team Members

| Student ID | Name (EN)                | Name (TH)               |
| ---------- | ------------------------ | ----------------------- |
| 67022951   | Ms. Achiraya Khieokanya  | นางสาวอชิรญา เขียวกันยะ |
| 67022940   | Ms. Hataichanok Tansakun | นางสาวหทัยชนก ตันสกุล   |
| 67023020   | Ms. Amornporn Onkhoksung | นางสาวอมราพร อ่อนโคกสูง |
| 67023086   | Mr. Aman Alikae          | นายอามาน อาลีแก         |

---

## Features

- ระบบ **Login / Logout** + Mock Login (role: staff / user)
- ระบบเช็คอิน–เช็คเอาต์ผ่าน **QR Code**
- บันทึก Log การใช้งานในฐานข้อมูล (`CheckinEvent`)
- ระบบ Pool Lock (ต้องเช็คเอาต์จากสระก่อนใช้งานสนามอื่น)
- หน้าเมนู **Staff Console** / **User Menu**
- หน้า **Report + API** แสดงข้อมูลสถิติและกราฟ
- รองรับ **Desktop / Mobile**
- ฟีเจอร์ถัดไป: **Borrow/Return, Booking, Export PDF/Excel, SSO**

---

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (Dev) → MySQL/MariaDB (Deploy)
- **Visualization:** Chart.js
- **Authentication:** Django Auth + Mock Login

---

## Project Structure

```bash
UP-Sports/
├── core/                    # Django app หลัก
│   ├── models.py            # CheckinEvent model
│   ├── views.py             # login_page, mock_login, api_check_event, api_checkins, ...
│   ├── urls.py              # routing
│   └── ...
├── templates/
│   ├── registration/
│   │   └── login.html       # หน้า Login หลัก
│   ├── staff_console.html
│   ├── user_menu.html
│   ├── choose.html
│   └── checkin_report.html
├── static/                  # css / js / img
├── db.sqlite3               # database (dev)
├── manage.py
└── README.md
```
