from fastapi import File, UploadFile, HTTPException, Depends,APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import SessionLocal, engine, Base
from models.Supplier import Supplier
import pandas as pd
from io import BytesIO
import os
from sqlalchemy import text
import logging
from datetime import datetime
import uuid
from pdf2image import convert_from_path
import easyocr
import numpy as np
import time
from transformers import pipeline

router = APIRouter()

# เตรียม EasyOCR ภาษาไทย+อังกฤษ (โหลด 1 ครั้ง)
ocr_reader = easyocr.Reader(['th', 'en'], gpu=False)

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "uploads"  # ✅ ใช้ uploads แทน
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

REQUIRED_COLUMNS = ["GENERICNAME"]

def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()

@router.on_event("startup")
def check_database_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("✅ Connected to the database successfully.")
    except Exception as e:
        logging.error("❌ Cannot connect to the database!")
        raise RuntimeError("Database connection failed during startup.")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} is not allowed.")

    contents = await file.read()

    try:
        df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"อ่านไฟล์ไม่สำเร็จ: {str(e)}")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"ขาดคอลัมน์: {', '.join(missing)}")

    try:
        for _, row in df.iterrows():
            generic = row.get("GENERICNAME")
            if pd.isna(generic):
                continue
            member = Supplier(
                GENERICNAME=checkNull(generic),
                HOSPDRUGCODE=checkNull(row.get("HOSPDRUGCODE")),
                PRODUCTCAT=is_int(row.get("PRODUCTCAT")),
                TMTID=is_int(row.get("TMTID")),
                SPECPREP=checkNull(row.get("SPECPREP")),
                TRADENAME=checkNull(row.get("TRADENAME")),
                DFSCODE=checkNull(row.get("DFSCODE")),
                DOSAGEFORM=checkNull(row.get("DOSAGEFORM")),
                STRENGTH=checkNull(row.get("STRENGTH")),
                CONTENT=checkNull(row.get("CONTENT")),
                UNITPRICE=is_float(row.get("UNITPRICE")),
                DISTRIBUTOR=checkNull(row.get("DISTRIBUTOR")),
                MANUFACTURER=checkNull(row.get("MANUFACTURER")),
                ISED=checkNull(row.get("ISED")),
                NDC24=checkNull(row.get("NDC24")),
                PACKSIZE=checkNull(row.get("PACKSIZE")),
                PACKPRICE=checkNull(row.get("PACKPRICE")),
                UPDATEFLAG=checkNull(row.get("UPDATEFLAG")),
                DATECHANGE=checkDate(row.get("DATECHANGE")),
                DATEUPDATE=checkDate(row.get("DATEUPDATE")),
                DATEEFFECTIVE=checkDate(row.get("DATEEFFECTIVE")),
                ISED_APPROVED=checkNull(row.get("ISED_APPROVED")),
                NDC24_APPROVED=checkNull(row.get("NDC24_APPROVED")),
                DATE_APPROVED=checkDate(row.get("DATE_APPROVED")),
                ISED_STATUS=is_int(row.get("ISED_STATUS"))
            )
            db.add(member)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # ✅ บันทึกไฟล์ลง uploads ด้วยชื่อไม่ซ้ำ
    name, ext = os.path.splitext(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_name = f"{name}_{timestamp}_{uuid.uuid4().hex[:6]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    return JSONResponse(
        content={
            "filename": unique_name,
            "saved_path": file_path,
            "message": "✅ File uploaded and saved to uploads folder successfully",
        }
    )

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