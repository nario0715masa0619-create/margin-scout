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
    
    console.log(`[DEBUG] All items collected: ${allItems.length}`);
    
    // バックエンド API に送信
    if (allItems.length > 0) {
      console.log(`[DEBUG] Sending POST to ${API_URL}/research-jobs/${jobId}/items`);
      const response = await fetch(`${API_URL}/research-jobs/${jobId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: allItems })
      });
      console.log(`[DEBUG] POST response status: ${response.status}`);
      const data = await response.json();
      console.log(`[DEBUG] POST response data:`, data);
    } else {
      console.log(`[DEBUG] No items to send (allItems.length = 0)`);
    }
    
    sendResponse({ status: 'success', count: allItems.length });
  } catch (error) {
    console.error(`[DEBUG] Error:`, error);
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
          
          // SPAのDOM描画（React/Vueなど）を待つために10秒遅延させる
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
                console.log(`[Extension Worker Log] Extracted ${results[0].result.length} items from ${platform}`);
                resolve(results[0].result);
              } else {
                console.log(`[Extension Worker Log] Extracted 0 items from ${platform}`);
                resolve([]);
              }
            });
          }, 10000); // 描画待機 10秒
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
  console.log(`[DEBUG] extractItems called for platform: ${platform}`);
  
  if (platform === 'mercari') {
    const links = document.querySelectorAll('a[href^="/item/m"]');
    console.log(`[DEBUG] Total links found: ${links.length}`);
    links.forEach((card, index) => {
      try {
        const href = card.getAttribute('href') || '';
        console.log(`[DEBUG] Card ${index}: href=${href}`);
        
        const url = href.startsWith('http') ? href : `https://jp.mercari.com${href}`;
        
        // aria-label から タイトルと価格を抽出
        const img = card.querySelector('img[alt], div[aria-label]');
        const ariaLabel = img?.getAttribute('aria-label') || img?.getAttribute('alt') || '';
        console.log(`[DEBUG] Card ${index}: ariaLabel=${ariaLabel}`);
        
        // "タイトル 説明 価格" 形式から抽出
        const parts = ariaLabel.split('\n');
        const title = parts[0]?.trim() || 'Unknown';
        const priceMatch = ariaLabel.match(/[\d,]+円/);
        const priceText = priceMatch ? priceMatch[0].replace(/[^\d]/g, '') : '0';
        const price = parseFloat(priceText);
        
        console.log(`[DEBUG] Card ${index}: title=${title}, price=${price}`);
        
        if (title && price > 0) {
          items.push({
            title: `[MERCARI] ${title}`,
            price: price,
            url: url,
            source: 'mercari'
          });
          console.log(`[DEBUG] ✅ Item added: ${title}`);
        }
      } catch (e) {
        console.error(`[DEBUG] Error at card ${index}:`, e);
      }
    });
    console.log(`[DEBUG] Total Mercari items extracted: ${items.length}`);
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
