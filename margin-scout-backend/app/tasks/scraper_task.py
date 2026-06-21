import logging
import asyncio
from app.celery_app import celery_app
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.research_job import JobStatus
from app.repositories.research_job_repository import research_job_repo
from app.services.domestic_scraper import DomesticScraperFactory

logger = logging.getLogger(__name__)

async def _run_all_scrapers(keyword: str):
    """eBayモックと国内ソース（Playwright）を並行してスクレイピング"""
    from playwright.async_api import async_playwright
    import time
    
    # Mock eBay search results
    ebay_items = [
        {
            "title": f"Mock Item {i+1} for {keyword}",
            "price": {"value": str(100 + (i * 10)), "currency": "USD"},
            "itemId": f"ebay_mock_{i+1}",
            "itemWebUrl": f"https://ebay.com/itm/mock_{i+1}",
            "image": {"imageUrl": "https://via.placeholder.com/150"},
            "source": "ebay"
        }
        for i in range(10)
    ]
    
    # 国内スクレイパーの初期化
    mercari = DomesticScraperFactory.get_scraper('mercari')
    yahoo_fril = DomesticScraperFactory.get_scraper('yahoo_fril')
    rakuma = DomesticScraperFactory.get_scraper('rakuma')
    
    # Playwrightのブラウザを起動して各スクレイパーにページ（タブ）を割り当て
    async with async_playwright() as p:
        logger.info("Launching Playwright Chromium browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page_m = await context.new_page()
        page_y = await context.new_page()
        page_r = await context.new_page()
        
        # 並行してスクレイピング実行
        logger.info(f"Starting parallel domestic scraping for '{keyword}'...")
        results = await asyncio.gather(
            mercari.scrape(keyword, page_m),
            yahoo_fril.scrape(keyword, page_y),
            rakuma.scrape(keyword, page_r),
            return_exceptions=True
        )
        
        await browser.close()
    
    mercari_items = results[0] if not isinstance(results[0], Exception) else []
    yahoo_items = results[1] if not isinstance(results[1], Exception) else []
    rakuma_items = results[2] if not isinstance(results[2], Exception) else []
    
    if isinstance(results[0], Exception): logger.error(f"Mercari Task Error: {results[0]}")
    if isinstance(results[1], Exception): logger.error(f"Yahoo Fril Task Error: {results[1]}")
    if isinstance(results[2], Exception): logger.error(f"Rakuma Task Error: {results[2]}")
    
    return {
        "ebay": ebay_items,
        "mercari": mercari_items,
        "yahoo_fril": yahoo_items,
        "rakuma": rakuma_items,
        "all_domestic": mercari_items + yahoo_items + rakuma_items
    }

@celery_app.task(name="run_research_job")
def run_research_job(job_id: str):
    logger.info(f"Starting research job: {job_id}")
    db: Session = SessionLocal()
    
    try:
        job = research_job_repo.get(db, id=job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
        
        job.status = JobStatus.running
        db.commit()
        
        keywords = ", ".join(job.conditions.get("keywords", []))
        logger.info(f"Searching for: {keywords}")
        
        # Asyncスクレイピングを実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scraped_data = loop.run_until_complete(_run_all_scrapers(keywords))
        loop.close()
        
        # UIエラーを避けるため、国内アイテムをeBay形式（candidateId, title, price, itemWebUrl）に変換
        all_items = scraped_data["ebay"].copy()
        
        for item in scraped_data["all_domestic"]:
            all_items.append({
                "title": f"[{item['source'].upper()}] {item['title']}",
                "price": {"value": str(item['price']), "currency": "JPY"},  # 国内はJPY
                "itemId": item.get('url', ''),  # candidateId としてURLを使用
                "itemWebUrl": item.get('url', ''),
                "image": {"imageUrl": "https://via.placeholder.com/150"},
                "source": item['source']
            })
            
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = len(all_items)
        job.matched_items = len(scraped_data["all_domestic"])
        job.result_summary = {"items": all_items}
        db.commit()
        logger.info(f"Job completed: {len(all_items)} total items")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = JobStatus.failed
        db.commit()
    finally:
        db.close()
