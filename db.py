# db.py: 판정 결과를 MariaDB에 저장하고 조회하는 함수
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()  # .env에서 접속 정보 읽기 (비밀번호를 코드에 쓰지 않음)

def _connect():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4',
    )

def save_result(image_name, label, defect_prob, machine_id=1):
    """판정 결과 1건을 저장"""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO inspections (machine_id, image_name, label, defect_prob) "
                "VALUES (%s, %s, %s, %s)",
                (machine_id, image_name, label, defect_prob),
            )
        conn.commit()
    finally:
        conn.close()

def get_history(limit=50):
    """최근 검사 이력을 최신순으로 조회"""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, inspected_at, machine_id, image_name, label, defect_prob "
                "FROM inspections ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()