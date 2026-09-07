import pymysql
import os
from typing import List, Dict, Optional
from datetime import datetime

# MySQL 연결 설정 (환경변수 또는 기본값)
# 로컬 개발 환경의 Express 서버(WAS)가 연결하는 DB 정보를 따름.
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")  
DB_NAME = os.getenv("DB_NAME", "vulnapp")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def book_appointment(patient_id: int, date_str: str, department: str) -> str:
    """환자의 진료를 예약합니다. date_str은 'YYYY-MM-DD HH:MM:SS' 형식이어야 합니다."""
    if not patient_id:
        return "환자 식별 정보를 확인할 수 없어 예약할 수 없습니다. 다시 로그인해 주세요."
        
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO appointments (patient_id, appointment_date, department, status) VALUES (%s, %s, %s, 'scheduled')"
            cursor.execute(sql, (patient_id, date_str, department))
        conn.commit()
        conn.close()
        return f"{date_str}에 {department} 진료 예약이 완료되었습니다."
    except Exception as e:
        return f"진료 예약 중 오류가 발생했습니다: {str(e)}"

def check_appointments(patient_id: int) -> str:
    """환자의 최근 진료 예약(최대 3건)을 조회합니다."""
    if not patient_id:
        return "환자 식별 정보를 확인할 수 없어 예약 내역을 조회할 수 없습니다."
        
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = "SELECT appointment_date, department, status FROM appointments WHERE patient_id = %s ORDER BY appointment_date DESC LIMIT 3"
            cursor.execute(sql, (patient_id,))
            rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "최근 진료 예약 내역이 없습니다."
            
        result = ["최근 진료 예약 내역(최대 3건)입니다:"]
        for row in rows:
            status_kr = "예약 완료" if row['status'] == 'scheduled' else "진료 완료" if row['status'] == 'completed' else "예약 취소"
            result.append(f"- {row['appointment_date']} | {row['department']} ({status_kr})")
        return "\n".join(result)
    except Exception as e:
        return f"예약 조회 중 오류가 발생했습니다: {str(e)}"

def check_medical_records(patient_id: int) -> str:
    """환자의 진료 기록이 있는지 확인합니다."""
    if not patient_id:
        return "환자 식별 정보를 확인할 수 없어 진료 기록을 조회할 수 없습니다."
        
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = "SELECT id FROM medical_records WHERE patient_id = %s LIMIT 1"
            cursor.execute(sql, (patient_id,))
            row = cursor.fetchone()
        conn.close()
        
        if not row:
            return "조회된 진료 기록이 없습니다."
            
        # 기록이 존재하면 병원 홈페이지의 진료기록 목록 바로가기 링크를 제공
        return "진료 기록이 존재합니다. 자세한 내역은 다음 링크에서 확인하실 수 있습니다.\n[진료 기록 바로가기](/records.html)"
    except Exception as e:
        return f"진료 기록 조회 중 오류가 발생했습니다: {str(e)}"
