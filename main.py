"""
FastAPI 금 데이터 대시보드 서버
- DataCollector 통합 실시간 데이터 수집
- 매 1초마다 자동 수집
- 단일 메인 대시보드 제공
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
from datetime import datetime, timezone, timedelta
import uvicorn

from data_collector import DataCollector
from db_manager import DatabaseManager

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_korean_time():
    """한국 시간 반환"""
    return datetime.now(KST)

app = FastAPI(title="🥇 금 데이터 실시간 대시보드", description="DataCollector 통합 실시간 금 데이터 모니터링")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 전역 컴포넌트
collector = DataCollector()
db_manager = DatabaseManager()

# 백그라운드 수집 상태
collection_running = False
collection_task = None
latest_data = None

async def background_data_collector():
    """백그라운드에서 1초마다 데이터 수집"""
    global collection_running, latest_data
    
    print("🚀 백그라운드 데이터 수집 시작 (1초 간격)")
    
    while collection_running:
        try:
            # DataCollector로 데이터 수집 및 저장
            await collector.collect_and_save_once()
            
            # 최신 데이터 캐시 업데이트
            latest_data = db_manager.get_latest_data()
            
        except Exception as e:
            print(f"❌ 백그라운드 수집 오류: {e}")
        
        # 1초 대기
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 백그라운드 수집 시작"""
    global collection_running, collection_task
    
    try:
        print("🔧 서버 시작 - 백그라운드 수집 초기화")
        collection_running = True
        collection_task = asyncio.create_task(background_data_collector())
        print("✅ 백그라운드 데이터 수집 시작됨")
    except Exception as e:
        print(f"❌ 백그라운드 수집 시작 실패: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 백그라운드 수집 정리"""
    global collection_running, collection_task
    
    print("🛑 서버 종료 - 백그라운드 수집 중단")
    collection_running = False
    
    if collection_task:
        collection_task.cancel()
        try:
            await collection_task
        except asyncio.CancelledError:
            pass
    
    print("✅ 백그라운드 수집 정리 완료")

@app.get("/", response_class=HTMLResponse)
async def main_dashboard(request: Request):
    """메인 대시보드 페이지"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/latest")
async def get_latest_data():
    """최신 데이터 API (캐시된 데이터 반환)"""
    global latest_data
    
    try:
        if latest_data is None:
            # 캐시가 없으면 DB에서 직접 조회
            latest_data = db_manager.get_latest_data()
        
        if latest_data:
            return JSONResponse(content={
                "success": True,
                "data": latest_data,
                "timestamp": get_korean_time().isoformat(),
                "collection_status": "running" if collection_running else "stopped"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "데이터가 없습니다",
                "timestamp": get_korean_time().isoformat(),
                "collection_status": "running" if collection_running else "stopped"
            })
            
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "timestamp": get_korean_time().isoformat(),
            "collection_status": "running" if collection_running else "stopped"
        })

@app.get("/api/status")
async def get_collection_status():
    """수집 상태 확인 API"""
    return JSONResponse(content={
        "collection_running": collection_running,
        "server_time": get_korean_time().isoformat(),
        "latest_data_available": latest_data is not None
    })

if __name__ == "__main__":
    print("🥇 금 데이터 실시간 대시보드 서버 시작")
    print("📊 메인 대시보드: http://localhost:8000/")
    print("🔄 실시간 API: http://localhost:8000/api/latest")
    print("📈 수집 상태: http://localhost:8000/api/status")
    print("⛔ 서버를 중단하려면 Ctrl+C를 누르세요")
    print("=" * 60)
    
    # uvicorn 서버 시작
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False,
        log_level="info"
    )