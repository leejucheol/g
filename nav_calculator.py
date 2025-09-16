"""NAV(순자산가치) 계산기
금현물 가격을 기준으로 ETF의 이론적 NAV를 계산
공식: NAV = (금현물가격 * 14,000) / 100,000주 = 금현물가격 * 0.14
"""

from datetime import datetime, timezone, timedelta

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)

class NAVCalculator:
    """NAV 계산기"""
    
    def __init__(self):
        # NAV 계산 상수
        self.gold_holding_per_cu = 14000  # 1CU당 금 보유량 (그램)
        self.total_shares = 100000  # 총 발행주식수 (10만주)
        self.nav_multiplier = self.gold_holding_per_cu / self.total_shares  # 0.14
        
        print(f"📊 NAV 계산기 초기화:")
        print(f"   - 1CU당 금 보유량: {self.gold_holding_per_cu:,}g")
        print(f"   - 총 발행주식수: {self.total_shares:,}주")
        print(f"   - NAV 계산 배수: {self.nav_multiplier}")
    
    def calculate_nav(self, gold_spot_price):
        """
        NAV 계산
        
        Args:
            gold_spot_price (float): 금현물 가격 (원/g)
            
        Returns:
            dict: NAV 계산 결과
        """
        try:
            if not gold_spot_price or gold_spot_price <= 0:
                return {
                    "nav_value": 0,
                    "gold_spot_price": 0,
                    "calculation_status": "금현물 가격 없음",
                    "timestamp": get_korean_time().isoformat()
                }
            
            # NAV = (금현물가격 * 14,000g) / 100,000주
            nav_value = gold_spot_price * self.nav_multiplier
            
            result = {
                "nav_value": round(nav_value, 2),
                "gold_spot_price": gold_spot_price,
                "calculation_formula": f"({gold_spot_price:,.0f} × {self.gold_holding_per_cu:,}) ÷ {self.total_shares:,}",
                "calculation_status": "계산 완료",
                "timestamp": get_korean_time().isoformat()
            }
            
            print(f"💰 NAV 계산: {gold_spot_price:,.0f}원/g → {nav_value:,.2f}원/주")
            return result
            
        except Exception as e:
            return {
                "nav_value": 0,
                "gold_spot_price": gold_spot_price,
                "calculation_status": f"계산 오류: {str(e)}",
                "timestamp": get_korean_time().isoformat()
            }
    
    def calculate_nav_with_all_data(self, market_data):
        """
        전체 시장 데이터를 받아서 NAV 계산
        
        Args:
            market_data (dict): 시장 데이터 (domestic, us_futures, gold_spot, usd_krw)
            
        Returns:
            dict: NAV 계산 결과와 추가 정보
        """
        try:
            # 금현물 데이터 추출
            gold_spot_data = market_data.get('gold_spot')
            if not gold_spot_data or not isinstance(gold_spot_data, dict):
                return self.calculate_nav(0)
            
            gold_spot_price = gold_spot_data.get('current_price', 0)
            
            # 기본 NAV 계산
            nav_result = self.calculate_nav(gold_spot_price)
            
            # 추가 정보 포함
            nav_result.update({
                "data_sources": {
                    "domestic_etf": market_data.get('domestic', {}).get('current_price', 0) if market_data.get('domestic') else 0,
                    "us_futures": market_data.get('us_futures', {}).get('current_price', 0) if market_data.get('us_futures') else 0,
                    "gold_spot": gold_spot_price,
                    "usd_krw": market_data.get('usd_krw', {}).get('current_price', 0) if market_data.get('usd_krw') else 0
                }
            })
            
            return nav_result
            
        except Exception as e:
            print(f"❌ NAV 계산 오류: {e}")
            return self.calculate_nav(0)
    
    def format_nav_for_display(self, nav_result):
        """
        대시보드 표시용 NAV 데이터 포맷팅 (계산된 값만 반환)
        
        Args:
            nav_result (dict): NAV 계산 결과
            
        Returns:
            dict: 단순한 NAV 값만 포함
        """
        try:
            nav_value = nav_result.get('nav_value', 0)
            
            return {
                "nav_value": nav_value
            }
            
        except Exception as e:
            print(f"❌ NAV 포맷팅 오류: {e}")
            return {
                "nav_value": 0
            }

# 테스트용 함수
def test_nav_calculator():
    """NAV 계산기 테스트"""
    print("=== NAV 계산기 테스트 ===")
    
    calc = NAVCalculator()
    
    # 테스트 데이터
    test_gold_prices = [150000, 160000, 170000, 0]
    
    for price in test_gold_prices:
        result = calc.calculate_nav(price)
        print(f"금현물: {price:,}원/g → NAV: {result['nav_value']:,.2f}원/주 ({result['calculation_status']})")
    
    print("\n=== 전체 데이터 테스트 ===")
    test_market_data = {
        'domestic': {'current_price': 21500},
        'us_futures': {'current_price': 2650},
        'gold_spot': {'current_price': 155000},
        'usd_krw': {'current_price': 1340}
    }
    
    result = calc.calculate_nav_with_all_data(test_market_data)
    print(f"전체 데이터 NAV 결과: {result}")

if __name__ == "__main__":
    test_nav_calculator()