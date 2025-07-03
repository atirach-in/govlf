from fastapi import HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from core.database import db
import time
import json
import csv

async def sync_data():
    driver = webdriver.Chrome()
    driver.get("https://www.gprocurement.go.th/new_index.html")

    # คลิกปุ่ม "ค้นหาขั้นสูง"
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, \"searchannounce('D')\")]"))
    ).click()

    time.sleep(10)  # รอโหลดข้อมูล

    columns = ['ลำดับ', 'หน่วยงาน', 'เรื่อง', 'วันที่ประกาศ', 'งบประมาณ', 'สถานะ', 'ประกาศที่เกี่ยวข้อง']
    all_data = []

    current_page = 1
    page_group_start = 1  # หน้าเริ่มต้นของกลุ่ม pagination (1, 6, 11, ...)
    tr_index_start = 1  # ใช้สำหรับกำหนด trDetail index

    while True:
        print(f"📄 กำลังดึงข้อมูลหน้าที่ {current_page} → trDetail{tr_index_start} - trDetail{tr_index_start + 9}")

        for i in range(tr_index_start, tr_index_start + 10):
            tr_id = f"trDetail{i}"
            try:
                row = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, tr_id))
                )
                tds = row.find_elements(By.TAG_NAME, "td")
                row_data = {}
                for col_name, td in zip(columns, tds):
                    row_data[col_name] = td.text.strip()
                row_data['หน้า'] = current_page
                all_data.append(row_data)
            except Exception as e:
                print(f"❌ ข้าม {tr_id} (ไม่พบหรือ timeout): {e}")
        
        
        # คำนวณเลขหน้าที่จะกดใน pagination ปัจจุบัน
        next_page_num = page_group_start + ((current_page - 1) % 5)

        # ถ้าถึงหน้าสุดท้ายของกลุ่ม (หารด้วย 5 ลงตัว) ต้องกด "ถัดไป" เพื่อไปกลุ่มหน้าใหม่
        if (current_page % 5) == 0:
            # กดปุ่ม "ถัดไป"
            try:
                next_button_td = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//td[@onclick and contains(@onclick, 'pageNext')]"))
                )
                # ตรวจสอบว่ามี onclick attribute หรือไม่ (ถ้ามีแสดงกดได้)
                onclick_attr = next_button_td.get_attribute("onclick")
                if onclick_attr and "pageNext" in onclick_attr:
                    print(f"current_page: {current_page} → กดปุ่ม 'ถัดไป'")
                    
                    driver.execute_script("arguments[0].click();", next_button_td)
                    time.sleep(3)  # รอโหลดข้อมูล
                    tr_index_start = 1  # รีเซต trDetail
                    current_page += 1
                    page_group_start += 5  # ขยับกลุ่มหน้าขึ้น 5
                else:
                    print(f"🚫 ไม่พบปุ่ม 'ถัดไป' หรือไม่สามารถกดได้: {onclick_attr} → หยุดดึงข้อมูล")
                    break
            except Exception as e:
                print(f"🚫 ไม่สามารถกดปุ่ม 'ถัดไป' ได้: {e} → หยุดดึงข้อมูล")
                break
        else:
            # คำนวณเลขหน้าที่จะกดในกลุ่ม
            next_page_to_click = page_group_start + ((current_page) % 5)  # หน้า ถัดไปที่ควรกด

            # ไม่กดปุ่มเลขหน้าปัจจุบันซ้ำ
            if next_page_to_click == current_page:
                print(f"current_page: {current_page} → อยู่หน้าปัจจุบัน ไม่ต้องกดปุ่มเลขหน้า")
                # เพิ่ม tr_index_start และ current_page ปกติ
                tr_index_start += 10
                current_page += 1
                continue

            try:
                print(f"current_page: {current_page} → กดปุ่มหน้า {next_page_to_click}")
                page_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        f"//td[@id='tdpage2' and @class='blue' and text()='{next_page_to_click}']"
                    ))
                )
                driver.execute_script("arguments[0].click();", page_btn)
                time.sleep(3)
                tr_index_start += 10
                current_page += 1
            except Exception as e:
                print(f"🚫 ไม่พบปุ่มหน้า {next_page_to_click} หรือกดไม่ได้: {e} → หยุดดึงข้อมูล")
                break

    # สร้าง timestamp ในรูปแบบ DDMMYYHHmm
    timestamp = datetime.now().strftime("%d%m%y%H%M")
    # สร้างชื่อไฟล์โดยใช้ timestamp
    filenameJSON = f"file_{timestamp}.json"

    # บันทึกข้อมูล JSON
    with open("./uploads/"+filenameJSON, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"✅ ดึงข้อมูลทั้งหมด {len(all_data)} แถว บันทึกลง egp_data.json เรียบร้อยแล้ว")
    driver.quit()

    # อ่านไฟล์ JSON
    with open('egp_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # สมมติ data เป็น list ของ dict
    # เช่น [{...}, {...}, ...]

    # กำหนดชื่อคอลัมน์ (header) จาก key ของ dict แรก
    header = data[0].keys()

    filenameCSV = f"file_{timestamp}.csv"
    # เขียนไฟล์ CSV
    with open("./uploads/"+filenameCSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)

    print("แปลง JSON เป็น CSV เรียบร้อยแล้ว")


    # Find all data in the collection
    all_data_db = await db["projects_gov"].find().to_list(length=None)

    #Loop array data
    for item in all_data:
        #Find project gov by เรื่อง from all_data_db
        project_gov = next((proj for proj in all_data_db if proj.get("เรื่อง") == item.get("เรื่อง")), None)
        if project_gov:
            # Update the project_gov with new data
            await db["projects_gov"].update_one(
                {"_id": project_gov["_id"]},
                {"$set": {
                    "name": item.get("เรื่อง"),
                    "deptName": item.get("หน่วยงาน"),
                    "announceData": item.get("วันที่ประกาศ"),
                    "budGet": item.get("งบประมาณ"),
                    "status": item.get("สถานะ"),
                    "relatedAnnouncement": item.get("ประกาศที่เกี่ยวข้อง")
                }}
            )
        else:
            # Insert new project_gov if not found
            await db["projects_gov"].insert_one({
                "name": item.get("เรื่อง"),
                "deptName": item.get("หน่วยงาน"),
                "announceData": item.get("วันที่ประกาศ"),
                "budGet": item.get("งบประมาณ"),
                "status": item.get("สถานะ"),
                "relatedAnnouncement": item.get("ประกาศที่เกี่ยวข้อง")
            })
        pass

    raise HTTPException(status_code=200, detail="Data scraping and conversion completed successfully.")
