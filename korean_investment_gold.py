"""한국투자증권 API 클래스 - 411060 금 종목 + 미국 금 선물"""
import requests
import json
import pickle
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)


class KoreanInvestmentGoldAPI:
    """한국투자증권 API - 411060 금 종목 + 금현물 종목 + 미국 금 선물 클래스"""
    
    def __init__(self):
        # API 설정 - .env 파일에서 로드
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.app_key = os.getenv("APP_KEY")
        self.app_secret = os.getenv("APP_SECRET")
        
        print(f"API 키 로드 상태: APP_KEY={'있음' if self.app_key else '없음'}, APP_SECRET={'있음' if self.app_secret else '없음'}")
        
        if not self.app_key or not self.app_secret:
            raise ValueError("APP_KEY와 APP_SECRET이 .env 파일에 설정되어야 합니다.")
        
        self.token_file = "token_data.pkl"
        self.access_token = None
        self.token_expire_time = None
        
        # 토큰 로드 시도
        self.load_token_from_file()
        
        # 토큰이 없거나 만료되었으면 새로 발급
        if not self.is_token_valid():
            print("토큰이 유효하지 않음. 새로 발급합니다.")
            self.get_access_token()
    
    def get_access_token(self):
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            result = response.json()
            print(result)
            
            if response.status_code == 200 and "access_token" in result:
                self.access_token = result["access_token"]
                # 토큰 만료시간 설정 (23시간 후) - 한국 시간 기준
                self.token_expire_time = get_korean_time() + timedelta(hours=23)
                
                self.save_token_to_file()
                print(f"새 토큰 발급 완료. 만료 시간: {self.token_expire_time}")
                return True
            else:
                print(f"토큰 발급 실패: {result}")
                return False
                
        except Exception as e:
            return False
    
    def save_token_to_file(self):
        """토큰을 파일에 저장"""
        token_data = {
            "access_token": self.access_token,
            "expire_time": self.token_expire_time
        }
        with open(self.token_file, 'wb') as f:
            pickle.dump(token_data, f)
    
    def load_token_from_file(self):
        """파일에서 토큰 로드"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as f:
                    token_data = pickle.load(f)
                self.access_token = token_data["access_token"]
                self.token_expire_time = token_data["expire_time"]
                print(f"저장된 토큰 불러옴. 만료 시간: {self.token_expire_time}")
            except Exception as e:
                pass  # 토큰 로드 오류는 조용히 처리
    
    def is_token_valid(self):
        """토큰 유효성 검사"""
        if not self.access_token or not self.token_expire_time:
            return False
        
        # 현재 한국 시간
        current_korean_time = get_korean_time()
        
        # token_expire_time이 timezone 정보가 없으면 KST로 간주
        if self.token_expire_time.tzinfo is None:
            # timezone 정보가 없는 경우 KST로 설정
            expire_time_with_tz = self.token_expire_time.replace(tzinfo=KST)
        else:
            expire_time_with_tz = self.token_expire_time
        
        return current_korean_time < expire_time_with_tz
    
    def get_all_gold_data(self):
        """411060 금 종목 + 미국 금 선물 데이터 모두 조회"""
        if not self.is_token_valid():
            self.get_access_token()
        
        # 411060 금 종목 데이터
        gold_etf_data = self.get_gold_411060_data()
        
        # 미국 금 선물 데이터
        us_gold_futures_data = self.get_us_gold_futures_data()
        
        return {
            "gold_etf_411060": gold_etf_data,
            "us_gold_futures": us_gold_futures_data,
            "timestamp": get_korean_time().isoformat()
        }
    
    def get_gold_411060_data(self, symbol = "411060"):
        """411060 금 종목 현재가 및 호가 데이터 조회 (호가 API 하나로 통합)"""
        if not self.is_token_valid():
            if not self.get_access_token():
                return "토큰을 재발급하세요. API 키를 확인해주세요."
        
        result = {
            "current_price": 0,
            "bid_price_1": 0,
            "bid_volume_1": 0,
            "ask_price_1": 0,
            "ask_volume_1": 0,
            "timestamp": get_korean_time().isoformat()
        }
        
        # 호가 조회 API로 현재가와 호가 정보 모두 가져오기
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "FHKST01010200"
            }
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
            
            response = requests.get(url, headers=headers, params=params)
            api_result = response.json()
            
            print(f"[API 응답] Status: {response.status_code}")
            print(f"[API 응답] 전체 응답: {api_result}")
            
            if response.status_code == 200 and api_result.get("rt_cd") == "0":
                output1 = api_result.get("output1", {})  # 호가 정보
                output2 = api_result.get("output2", {})  # 현재가 정보
                
                # 현재가 정보 (output2에서)
                current_price = float(output2.get("stck_prpr", 0))
                
                # 호가 정보 (output1에서)
                bid_price = float(output1.get("bidp1", 0))
                bid_volume = int(output1.get("bidp_rsqn1", 0))
                ask_price = float(output1.get("askp1", 0))
                ask_volume = int(output1.get("askp_rsqn1", 0))
                
                result.update({
                    "current_price": current_price,
                    "bid_price_1": bid_price,
                    "bid_volume_1": bid_volume,
                    "ask_price_1": ask_price,
                    "ask_volume_1": ask_volume
                })
                
                print(f"✅ [한국투자] 411060 - 현재가: {current_price:,}원, 매수: {bid_price:,}원({bid_volume:,}주), 매도: {ask_price:,}원({ask_volume:,}주)")
            else:
                print(f"[오류] rt_cd: {api_result.get('rt_cd')}, msg_cd: {api_result.get('msg_cd')}, msg1: {api_result.get('msg1')}")
                if api_result.get("rt_cd") == "1":
                    return "토큰이 만료되었습니다. 토큰을 재발급하세요."
                
        except Exception as e:
            return f"API 호출 오류: {str(e)}. 토큰을 재발급하세요."
        
        return result
    
    def get_gd_gold_spot(self, symbol="04020000"):
        """한국투자증권 금현물 데이터 조회 - 04020000 (99.99% 순도 1kg 금현물)"""
        if not self.is_token_valid():
            if not self.get_access_token():
                return "토큰을 재발급하세요. API 키를 확인해주세요."

        result = {
            "current_price": 0,
            "bid_price_1": 0,
            "bid_volume_1": 0,
            "ask_price_1": 0,
            "ask_volume_1": 0,
            "timestamp": get_korean_time().isoformat()
        }

        try:
            print(f"🔍 금현물 시도: symbol={symbol}, tr_id=KRD040200002")
            
            # 금현물용 다른 엔드포인트 시도
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "KRD040200002"  # 한투 금현물 전용 TR ID
            }
            params = {
                "fid_cond_mrkt_div_code": "J",  # 장내
                "fid_input_iscd": symbol
            }

            response = requests.get(url, headers=headers, params=params)
            api_result = response.json()
            print(f"[금현물 API 응답] Status: {response.status_code}, rt_cd: {api_result.get('rt_cd')}")
            print(f"[금현물 API 전체 응답] {api_result}")
            
            if response.status_code == 200 and api_result.get("rt_cd") == "0":
                output1 = api_result.get("output1", {})
                output2 = api_result.get("output2", {})
                current_price = float(output2.get("stck_prpr", 0))
                
                if current_price > 0:
                    bid_price = float(output1.get("bidp1", 0))
                    bid_volume = int(output1.get("bidp_rsqn1", 0))
                    ask_price = float(output1.get("askp1", 0))
                    ask_volume = int(output1.get("askp_rsqn1", 0))
                    
                    result.update({
                        "current_price": current_price,
                        "bid_price_1": bid_price,
                        "bid_volume_1": bid_volume,
                        "ask_price_1": ask_price,
                        "ask_volume_1": ask_volume
                    })
                    
                    print(f"✅ [한국투자] 금현물({symbol}) - 현재가: {current_price:,}원, 매수: {bid_price:,}원({bid_volume:,}), 매도: {ask_price:,}원({ask_volume:,})")
                    return result
                else:
                    print(f"⚠️  {symbol}: 현재가가 0원")
            else:
                if api_result.get("rt_cd") == "1":
                    print(f"❌ {symbol}: 토큰 오류")
                    return "토큰이 만료되었습니다. 토큰을 재발급하세요."
                else:
                    print(f"❌ {symbol}: rt_cd={api_result.get('rt_cd')}, msg={api_result.get('msg1')}")
                        
        except Exception as e:
            print(f"❌ {symbol} 시도 중 오류: {str(e)}")
        
        # 실패한 경우
        print(f"⚠️  금현물({symbol}) 데이터 조회 실패")
        return result
    
    def get_us_gold_futures_data(self, symbol = "CMX"):
        """미국 금 선물 데이터 조회 (COMEX/CME - 시카고상품거래소)"""
        if not self.is_token_valid():
            if not self.get_access_token():
                return "토큰을 재발급하세요. API 키를 확인해주세요."
        
        # 해외선물 현재가 조회 API 사용
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "HHDFS76200200"  # 해외지수/선물 현재가 시세
        }
        
        params = {
            "SYMB": "GC",     # 금 선물 심볼 (Gold Continuous)
            "EXCD": symbol     # COMEX (시카고상품거래소)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            print(result)
            
            if response.status_code == 200 and result.get("rt_cd") == "0":
                output = result.get("output", {})
                
                current_price = float(output.get("last", 0))
                bid_price = float(output.get("bid", 0))
                ask_price = float(output.get("ask", 0))
                bid_volume = int(output.get("bid_size", 0))
                ask_volume = int(output.get("ask_size", 0))
                
                print(f"✅ [한국투자] 미국 금선물(COMEX) - 현재가: ${current_price}, 매수: ${bid_price}({bid_volume}), 매도: ${ask_price}({ask_volume})")
                
                return {
                    "current_price": current_price,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "bid_volume": bid_volume,
                    "ask_volume": ask_volume,
                    "timestamp": get_korean_time().isoformat()
                }

        except Exception as e:
            return "시장 시간 외이거나 심볼 오류일 수 있음"