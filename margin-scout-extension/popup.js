document.addEventListener('DOMContentLoaded', () => {
  const statusElement = document.getElementById('status');
  
  // バックエンドから scrape 指令を受け取った場合
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'startScrape') {
      statusElement.textContent = `Scraping: ${request.keyword}...`;
      
      // background.js に scrape 指令を送る
      chrome.runtime.sendMessage({
        action: 'scrape',
        keyword: request.keyword,
        jobId: request.jobId
      }, (response) => {
        if (response.status === 'success') {
          statusElement.textContent = `✓ Scraped ${response.count} items`;
        } else {
          statusElement.textContent = `✗ Error: ${response.message}`;
        }
      });
    }
  });
  
  // 初期状態
  statusElement.textContent = 'Waiting for search command...';
});
