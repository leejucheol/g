"""데이터베이스 전용 관리 클래스"""
import sqlite3
from datetime import datetime, timezone, timedelta

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)


class DatabaseManager:
    """SQLite 데이터베이스 전용 관리"""
    
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 통합 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gold_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    usd_krw_rate REAL,
                    domestic_current_price REAL,
                    domestic_bid_price_1 REAL,
                    domestic_bid_volume_1 INTEGER,
                    domestic_ask_price_1 REAL,
                    domestic_ask_volume_1 INTEGER,
                    us_futures_current_price REAL,
                    us_futures_bid_price_1 REAL,
                    us_futures_bid_volume_1 INTEGER,
                    us_futures_ask_price_1 REAL,
                    us_futures_ask_volume_1 INTEGER,
                    domestic_gold_spot_current_price REAL,
                    domestic_gold_spot_bid_price_1 REAL,
                    domestic_gold_spot_bid_volume_1 INTEGER,
                    domestic_gold_spot_ask_price_1 REAL,
                    domestic_gold_spot_ask_volume_1 INTEGER,
                    nav_value REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
    
    def save_market_data(self, domestic_data=None, us_futures_data=None, gold_spot_data=None, nav_data=None, usd_krw_data=None):
        """수집된 시장 데이터를 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 한국시간으로 created_at 설정
            korean_time = get_korean_time().strftime('%Y-%m-%d %H:%M:%S')
            timestamp = get_korean_time().isoformat()

            # 환율 데이터 추출
            usd_krw_rate = usd_krw_data.get('current_price') if usd_krw_data else None

            # 데이터 추출 (안전하게)
            domestic_current = domestic_data.get('current_price') if domestic_data else None
            domestic_bid = domestic_data.get('bid_price_1') if domestic_data else None
            domestic_bid_vol = domestic_data.get('bid_volume_1') if domestic_data else None
            domestic_ask = domestic_data.get('ask_price_1') if domestic_data else None
            domestic_ask_vol = domestic_data.get('ask_volume_1') if domestic_data else None
            
            us_current = us_futures_data.get('current_price') if us_futures_data else None
            us_bid = us_futures_data.get('bid_price') if us_futures_data else None
            us_bid_vol = us_futures_data.get('bid_volume') if us_futures_data else None
            us_ask = us_futures_data.get('ask_price') if us_futures_data else None
            us_ask_vol = us_futures_data.get('ask_volume') if us_futures_data else None
            
            # 금현물 데이터 추출
            spot_current = gold_spot_data.get('current_price') if gold_spot_data else None
            spot_bid = gold_spot_data.get('bid_price_1') if gold_spot_data else None
            spot_bid_vol = gold_spot_data.get('bid_volume_1') if gold_spot_data else None
            spot_ask = gold_spot_data.get('ask_price_1') if gold_spot_data else None
            spot_ask_vol = gold_spot_data.get('ask_volume_1') if gold_spot_data else None
            
            # NAV 데이터 추출 (계산된 값만)
            nav_value = nav_data.get('nav_value') if nav_data else None

            # 데이터 삽입            
            cursor.execute('''
                INSERT INTO gold_data (
                    timestamp, usd_krw_rate, domestic_current_price, domestic_bid_price_1, 
                    domestic_bid_volume_1, domestic_ask_price_1, domestic_ask_volume_1,
                    us_futures_current_price, us_futures_bid_price_1, us_futures_bid_volume_1,
                    us_futures_ask_price_1, us_futures_ask_volume_1,
                    domestic_gold_spot_current_price, domestic_gold_spot_bid_price_1, 
                    domestic_gold_spot_bid_volume_1, domestic_gold_spot_ask_price_1, domestic_gold_spot_ask_volume_1,
                    nav_value,
                    usd_krw_rate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, usd_krw_rate, domestic_current, domestic_bid, domestic_bid_vol,
                domestic_ask, domestic_ask_vol, us_current, us_bid, us_bid_vol,
                us_ask, us_ask_vol, spot_current, spot_bid, spot_bid_vol,
                spot_ask, spot_ask_vol, nav_value,
                korean_time
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")
            return False
    
    def get_data_count(self):
        """총 데이터 개수 반환"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM gold_data")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            return 0

    def get_latest_data(self, limit=10):
        """최근 데이터 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM gold_data 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def show_latest_data(self, limit=5):
        """최근 데이터 조회 및 출력"""
        print(f"\n최근 {limit}개 데이터:")
        data = self.get_latest_data(limit)
        
        for i, row in enumerate(data, 1):
            print(f"\n[{i}] {row['timestamp']}")
            if row['usd_krw_rate']:
                print(f"    USD/KRW: {row['usd_krw_rate']:,.2f}원")
            if row['domestic_current_price']:
                print(f"    국내금ETF: {row['domestic_current_price']:,}원")
            if row['us_futures_current_price']:
                print(f"    미국금선물: ${row['us_futures_current_price']:,.2f}")
            
