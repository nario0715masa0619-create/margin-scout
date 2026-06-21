// MarginScout API エンドポイント
const API_URL = 'https://spirited-flexibility-production-b48b.up.railway.app/api';

// ✅ 外部ウェブページ（Vue アプリ）からのメッセージを受け取る
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
  console.log('📨 External message received:', request);
  
  if (request.action === 'scrape') {
    const keyword = request.keyword;
    const jobId = request.jobId;
    const sources = request.sources || ['mercari', 'rakuma', 'yahoo_flea'];
    
    console.log(`🔍 Starting scrape for keyword: "${keyword}", jobId: "${jobId}", sources:`, sources);
    
    scrapeAllSites(keyword, jobId, sources, sendResponse);
    return true; // 非同期レスポンス用
  }
});

// ✅ 拡張機能内部（popup.js など）からのメッセージも受け取る
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 Internal message received:', request);
  
  if (request.action === 'scrape') {
    const keyword = request.keyword;
    const jobId = request.jobId;
    const sources = request.sources || ['mercari', 'rakuma', 'yahoo_flea'];
    
    console.log(`🔍 Starting scrape for keyword: "${keyword}", jobId: "${jobId}", sources:`, sources);
    
    scrapeAllSites(keyword, jobId, sources, sendResponse);
    return true; // 非同期レスポンス用
  }
});

// スクレイピング処理（共通関数）
async function scrapeAllSites(keyword, jobId, sources, sendResponse) {
  try {
    const promises = [];
    if (sources.includes('mercari')) {
      promises.push(scrapeMercariWithTab(keyword));
    }
    if (sources.includes('rakuma')) {
      promises.push(scrapeRakumaWithTab(keyword));
    }
    if (sources.includes('yahoo_flea')) {
      promises.push(scrapeYahooFleaWithTab(keyword));
    }
    
    const results = await Promise.all(promises);
    
    const allItems = results.flat();
    
    // バックエンド API に送信
    await fetch(`${API_URL}/research-jobs/${jobId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: allItems })
    });
    
    sendResponse({ status: 'success', count: allItems.length });
  } catch (error) {
    console.error('Scraping/API error:', error);
    sendResponse({ status: 'error', message: error.message });
  }
}

async function scrapeMercariWithTab(keyword) {
  const url = `https://jp.mercari.com/search?keyword=${encodeURIComponent(keyword)}&order=NEWEST`;
  return scrapeWithContentScript(url, 'mercari');
}

async function scrapeRakumaWithTab(keyword) {
  const url = `https://item.rakuma.com/search?keyword=${encodeURIComponent(keyword)}&sort=recently_updated`;
  return scrapeWithContentScript(url, 'rakuma');
}

async function scrapeYahooFleaWithTab(keyword) {
  const url = `https://paypayfleamarket.yahoo.co.jp/search/${encodeURIComponent(keyword)}`;
  return scrapeWithContentScript(url, 'yahoo_flea');
}

async function scrapeWithContentScript(url, platform) {
  return new Promise((resolve, reject) => {
    // 不可視タブを開く
    chrome.tabs.create({ url: url, active: false }, (tab) => {
      const tabId = tab.id;
      
      // ページ読み込み完了を待つ
      const onUpdated = (updatedTabId, changeInfo) => {
        if (updatedTabId === tabId && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(onUpdated);
          
          // SPAのDOM描画（React/Vueなど）を待つために4秒遅延させる
          setTimeout(() => {
            // Content Script を実行して DOM を抽出
            chrome.scripting.executeScript({
              target: { tabId: tabId },
              function: extractItems,
              args: [platform]
            }, (results) => {
              // タブを閉じる (存在チェック後に安全に削除)
              if (tabId) {
                chrome.tabs.get(tabId, (tab) => {
                  if (chrome.runtime.lastError) {
                    console.log(`Tab ${tabId} already closed`);
                  } else {
                    chrome.tabs.remove(tabId, () => {
                      const e = chrome.runtime.lastError; // エラーを握り潰す
                    });
                  }
                });
              }
              
              if (results && results[0] && results[0].result) {
                resolve(results[0].result);
              } else {
                resolve([]);
              }
            });
          }, 4000); // 描画待機 4秒
        }
      };
      
      chrome.tabs.onUpdated.addListener(onUpdated);
      
      // タイムアウト（120秒に変更）
      setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(onUpdated);
        if (tabId) {
          chrome.tabs.get(tabId, (tab) => {
            if (chrome.runtime.lastError) {
              console.log(`Tab ${tabId} already closed`);
            } else {
              chrome.tabs.remove(tabId, () => {
                const e = chrome.runtime.lastError;
              });
            }
          });
        }
        reject(new Error(`Scrape timeout for ${platform}`));
      }, 120000);
    });
  });
}

// Content Script で実行される関数（ページ内のDOMを直接読み取る）
function extractItems(platform) {
  const items = [];
  
  if (platform === 'mercari') {
    document.querySelectorAll('a[data-testid="product-card-anchor"]').forEach(card => {
      try {
        const title = card.querySelector('h2')?.textContent?.trim() || '';
        const priceText = card.querySelector('span')?.textContent?.match(/[\d,]+/)?.[0] || '0';
        const price = parseFloat(priceText.replace(/,/g, ''));
        const href = card.getAttribute('href') || '';
        const url = href.startsWith('http') ? href : `https://jp.mercari.com${href}`;
        
        if (title && price > 0) {
          items.push({
            title: `[MERCARI] ${title}`,
            price: price,
            url: url,
            source: 'mercari'
          });
        }
      } catch (e) {
        console.debug('Mercari parse error:', e);
      }
    });
  } else if (platform === 'rakuma') {
    document.querySelectorAll('div.item-card, a.item-cell').forEach(card => {
      try {
        const titleElem = card.querySelector('h3, .item-title, a');
        const title = titleElem?.textContent?.trim() || '';
        const priceText = card.querySelector('span, .price')?.textContent?.match(/[\d,]+/)?.[0] || '0';
        const price = parseFloat(priceText.replace(/,/g, ''));
        const linkElem = card.tagName === 'A' ? card : card.querySelector('a');
        const href = linkElem?.getAttribute('href') || '';
        const url = href.startsWith('http') ? href : `https://item.rakuma.com${href}`;
        
        if (title && price > 0) {
          items.push({
            title: `[RAKUMA] ${title}`,
            price: price,
            url: url,
            source: 'rakuma'
          });
        }
      } catch (e) {
        console.debug('Rakuma parse error:', e);
      }
    });
  } else if (platform === 'yahoo_flea') {
    document.querySelectorAll('a[href*="/item/"]').forEach(card => {
      try {
        const titleElem = card.querySelector('[class*="Title"], img[alt]');
        const title = titleElem?.textContent?.trim() || titleElem?.getAttribute('alt') || '';
        const priceText = card.textContent?.match(/[\d,]+円/)?.[0]?.replace(/円/, '').replace(/,/g, '') || card.textContent?.match(/[\d,]+/)?.[0] || '0';
        const price = parseFloat(priceText);
        const href = card.getAttribute('href') || '';
        const url = href.startsWith('http') ? href : `https://paypayfleamarket.yahoo.co.jp${href}`;
        
        if (title && price > 0) {
          items.push({
            title: `[YAHOO FLEA] ${title}`,
            price: price,
            url: url,
            source: 'yahoo_flea'
          });
        }
      } catch (e) {
        console.debug('Yahoo Flea parse error:', e);
      }
    });
  }
  
  return items;
}
