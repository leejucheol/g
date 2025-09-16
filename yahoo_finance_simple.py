"""Yahoo Finance API - USD/KRW 환율 클래스"""
import requests
import json
from datetime import datetime, timezone, timedelta

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)


class YahooFinanceAPI:
    """Yahoo Finance USD/KRW 환율 API"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.symbol = "USDKRW=X"
    
    def get_usd_krw_rate(self):
        """USD/KRW 환율 조회"""
        try:
            url = f"{self.base_url}/{self.symbol}"
            
            params = {
                "interval": "1m",
                "range": "1d"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and "chart" in data:
                chart = data["chart"]["result"][0]
                meta = chart["meta"]
                current_price = meta.get("regularMarketPrice", 0)
                
                if current_price > 0:
                    print(f"[Yahoo Finance] USD/KRW: {current_price:,.2f}원")
                    return {
                        "current_price": current_price,
                        "timestamp": get_korean_time().isoformat()
                    }
                else:
                    print("Yahoo Finance: 유효하지 않은 가격 데이터")
                    return None
            else:
                print(f"Yahoo Finance API 오류: {data}")
                return None
        except Exception as e:
            print(f"[Yahoo Finance ERROR] 환율 조회 실패: {e}")
            return None
