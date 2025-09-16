"""실시간 데이터 수집기 - API 호출 전용"""
import asyncio
import time
from datetime import datetime, timezone, timedelta
from korean_investment_gold import KoreanInvestmentGoldAPI
from yahoo_finance_simple import YahooFinanceAPI
from db_manager import DatabaseManager
from nav_calculator import NAVCalculator

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)


class DataCollector:
    """실시간 금 데이터 수집 전용 클래스"""
    
    def __init__(self):
        # API 클라이언트 초기화
        self.korean_api = KoreanInvestmentGoldAPI()
        self.yahoo_api = YahooFinanceAPI()
        
        # 데이터베이스 매니저 초기화
        self.db_manager = DatabaseManager()
        
        # NAV 계산기 초기화
        self.nav_calculator = NAVCalculator()
        
        self.running = False
    
    async def collect_all_data(self):
        """모든 데이터 수집 (저장은 별도)"""
        collection_time = get_korean_time()
        
        print(f"\n📡 데이터 수집 시작: {collection_time.strftime('%H:%M:%S.%f')[:-3]}")
        
        domestic_data = None
        us_futures_data = None
        gold_spot_data = None
        usd_krw_data = None
        
        # 1️⃣ 국내 금 ETF 데이터 수집
        try:
            domestic_result = self.korean_api.get_gold_411060_data()
            
            if isinstance(domestic_result, dict):
                current_price = domestic_result.get('current_price', 0)
                bid_price = domestic_result.get('bid_price_1', 0)
                ask_price = domestic_result.get('ask_price_1', 0)
                
                if current_price > 0 or bid_price > 0 or ask_price > 0:
                    domestic_data = domestic_result
                else:
                    print(f"❌ 국내 금ETF: 모든 가격 정보가 0")
            else:
                print(f"❌ 국내 금ETF: {domestic_result}")
        except Exception as e:
            print(f"❌ 국내 금ETF 수집 실패: {e}")
        
        # 2️⃣ 미국 금 선물 데이터 수집
        try:
            us_result = self.korean_api.get_us_gold_futures_data()
            if isinstance(us_result, dict) and us_result.get('current_price', 0) > 0:
                us_futures_data = us_result
            else:
                print(f"❌ 미국 금선물: {us_result}")
        except Exception as e:
            print(f"❌ 미국 금선물 수집 실패: {e}")
            
        # 3️⃣ 국내 금현물 데이터 수집
        try:
            spot_result = self.korean_api.get_gd_gold_spot() # "04020000"를 작성할지 말지
            if isinstance(spot_result, dict) and spot_result.get('current_price', 0) > 0:
                gold_spot_data = spot_result
            else:
                print(f"❌ 국내 금현물: {spot_result}")
        except Exception as e:
            print(f"❌ 국내 금현물 수집 실패: {e}")
        
        # 4️⃣ USD/KRW 환율 데이터 수집
        try:
            usd_result = self.yahoo_api.get_usd_krw_rate()
            if isinstance(usd_result, dict) and usd_result.get('current_price', 0) > 0:
                usd_krw_data = usd_result
                print(f"✅ USD/KRW: {usd_krw_data['current_price']:,.2f}원")
            else:
                print(f"❌ USD/KRW 수집 실패")
        except Exception as e:
            print(f"❌ USD/KRW 수집 실패: {e}")
        
        # 5️⃣ NAV 계산
        nav_data = None
        try:
            # 수집된 모든 데이터를 기준으로 NAV 계산
            market_data_for_nav = {
                'domestic': domestic_data,
                'us_futures': us_futures_data,
                'gold_spot': gold_spot_data,
                'usd_krw': usd_krw_data
            }
            
            nav_result = self.nav_calculator.calculate_nav_with_all_data(market_data_for_nav)
            nav_data = self.nav_calculator.format_nav_for_display(nav_result)
            
            if nav_data and nav_data.get('nav_value', 0) > 0:
                print(f"✅ NAV 계산: {nav_data['nav_value']:,.2f}원/주")
            else:
                print(f"❌ NAV 계산: 금현물 데이터 부족")
                
        except Exception as e:
            print(f"❌ NAV 계산 실패: {e}")
        
        return {
            'domestic': domestic_data,
            'us_futures': us_futures_data,
            'gold_spot': gold_spot_data,
            'usd_krw': usd_krw_data,
            'nav': nav_data,
            'timestamp': collection_time
        }
    
    async def collect_and_save_once(self):
        """데이터 수집 + 저장 (한 번)"""
        # 데이터 수집
        collected_data = await self.collect_all_data()
        
        # 최소 하나의 데이터라도 있으면 저장
        if any([collected_data['domestic'], collected_data['us_futures'], collected_data['gold_spot'], collected_data['nav'], collected_data['usd_krw']]):
            try:
                success = self.db_manager.save_market_data(
                    domestic_data=collected_data['domestic'],
                    us_futures_data=collected_data['us_futures'],
                    gold_spot_data=collected_data['gold_spot'],
                    nav_data=collected_data['nav'],
                    usd_krw_data=collected_data['usd_krw']
                )
                
                if success:
                    print(f"💾 데이터베이스 저장 완료")
                else:
                    print(f"❌ 데이터베이스 저장 실패")
                    
            except Exception as e:
                print(f"❌ 데이터베이스 저장 오류: {e}")
        else:
            print("⚠️  수집된 유효 데이터 없음")
        
        return collected_data
    
    async def start_real_time_collection(self):
        """1초마다 실시간 수집 + 저장"""
        print("\n" + "="*80)
        print(" 실시간 금 데이터 수집 시작!")
        print("="*80)
        print(" 수집 주기: 1초")
        print(" 대상: 411060 금ETF + 미국 금선물 + 국내 금현물 + USD/KRW")
        print(" 중단: Ctrl+C")
        print("="*80)
        
        self.running = True
        count = 0
        
        try:
            while self.running:
                count += 1
                start_time = time.time()
                
                print(f"\n[{count:04d}회차]", end=" ")
                await self.collect_and_save_once()
                
                # 1초 주기 맞추기
                elapsed = time.time() -start_time
                sleep_time = max(0, 1.0 - elapsed)
                
                if sleep_time > 0:
                    print(f"  수집 소요: {elapsed:.3f}초, {sleep_time:.3f}초 대기")
                    await asyncio.sleep(sleep_time)
                else:
                    print(f"⚠️  수집 소요: {elapsed:.3f}초 (1초 초과)")
                
        except KeyboardInterrupt:
            print(f"\n\n 사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n\n 수집 중 오류: {e}")
        finally:
            self.running = False
            print(f"\n 수집 요약:")
            print(f"  - 총 수집 횟수: {count}회")
            print(f"  - 총 데이터 개수: {self.db_manager.get_data_count()}개")
            print("="*80)
    
    def stop_collection(self):
        """수집 중단"""
        self.running = False

