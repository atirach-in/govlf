from fastapi import File, UploadFile, HTTPException, Depends,APIRouter
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
import os
import logging
from datetime import datetime
import uuid
from pdf2image import convert_from_path
import easyocr
import numpy as np
import time
from transformers import pipeline
from controllers import scraping

router = APIRouter()

# เตรียม EasyOCR ภาษาไทย+อังกฤษ (โหลด 1 ครั้ง)
ocr_reader = easyocr.Reader(['th', 'en'], gpu=False)

UPLOAD_DIR = "uploads"  # ✅ ใช้ uploads แทน
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

REQUIRED_COLUMNS = ["GENERICNAME"]

@router.post("/sync-data/")
async def sync_data():
    try:
        # เรียกใช้ฟังก์ชัน sync_data จาก controllers.scraping
        await scraping.sync_data()
        return JSONResponse(status_code=200, content={"message": "Data scraping and conversion completed successfully."})
    except Exception as e:
        logging.error(f"Error during data scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data scraping failed: {str(e)}")

@router.post("/ocr-pdf/")
async def ocr_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF เท่านั้น")

    # สร้างชื่อไฟล์ PDF และ TXT ไม่ซ้ำ
    file_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    txt_path = os.path.join(UPLOAD_DIR, f"{file_id}.txt")

    # บันทึก PDF ชั่วคราว
    contents = await file.read()
    with open(pdf_path, "wb") as f:
        f.write(contents)

    try:
        # แปลง PDF เป็นภาพ
        images = convert_from_path(pdf_path, dpi=200)

        # อ่าน OCR ทีละหน้า
        full_text = ""
        for i, img in enumerate(images):
            start = time.time()
            img_np = np.array(img)
            text_lines = ocr_reader.readtext(img_np, detail=0)
            page_text = "\n".join(text_lines)
            full_text += f"\n\n--- หน้าที่ {i+1} ---\n{page_text}"
            print(f"หน้า {i+1} ใช้เวลา: {time.time() - start:.2f} วินาที")

        # เขียนไฟล์ .txt
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        return JSONResponse({
            "message": "✅ OCR สำเร็จ",
            "output_txt": txt_path
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR ล้มเหลว: {str(e)}")



# ฟังก์ชันช่วย
def checkDate(date_str):
    if date_str is None or (isinstance(date_str, float) and pd.isna(date_str)):
        return None
    if isinstance(date_str, str) and date_str.strip() == "":
        return None
    try:
        return pd.to_datetime(date_str).date()
    except Exception:
        return None

def checkNull(value):
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return str(value)

def is_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def is_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def main():
    # โหลดโมเดลแก้คำผิด
    spell_checker = pipeline(
        "text2text-generation",
        model="tansongyang/thai-spell-check",
        tokenizer="tansongyang/thai-spell-check"
    )

    # ข้อความตัวอย่าง (จาก OCR หรือพิมพ์ผิด)
    input_text = "ฉันกำลังพิมพ์ข้อความทีผิดวรรณะยุคต์"

    # ประมวลผล
    result = spell_checker(
        input_text,
        max_length=128,
        clean_up_tokenization_spaces=True
    )[0]['generated_text']

    # แสดงผล
    print("🔍 ก่อนแก้ :", input_text)
    print("✅ หลังแก้ :", result)

if __name__ == "__main__":
    main()