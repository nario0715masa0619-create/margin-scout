export interface ExtractedItem {
  title: string
  price_jpy: number
  url: string
  seller_name?: string
  condition?: string
  image_url?: string
  fetched_at: string
}

export const MercariParser = {
  isListPage(): boolean {
    // URL パターンで一覧ページ判定
    return /mercari\.jp\/search/.test(window.location.href)
  },

  extractItems(): ExtractedItem[] {
    const items: ExtractedItem[] = []

    // Mercari の商品カード要素を取得
    const productCards = document.querySelectorAll("[data-testid='product-card-anchor']")

    productCards.forEach((card) => {
      try {
        // 各要素を抽出
        const titleEl = card.querySelector("h2, div[class*='name']")
        const priceEl = card.querySelector("[class*='price'], span[class*='¥']")
        const urlEl = card.getAttribute("href")
        const imgEl = card.querySelector("img")

        if (titleEl && priceEl && urlEl) {
          const title = titleEl.textContent?.trim() || ""
          const priceText = priceEl.textContent?.replace(/[^\d]/g, "") || "0"
          const price = parseInt(priceText, 10)

          items.push({
            title,
            price_jpy: price,
            url: new URL(urlEl, window.location.origin).href,
            image_url: imgEl?.src || undefined,
            condition: "new", // TODO: Mercari から condition を抽出
            seller_name: undefined, // TODO: seller 情報を抽出
            fetched_at: new Date().toISOString(),
          })
        }
      } catch (e) {
        console.warn("Failed to extract item:", e)
      }
    })

    return items
  },
}

export const YahooAuctionParser = {
  isListPage(): boolean {
    return /auctions\.yahoo\.co\.jp\/search/.test(window.location.href)
  },

  extractItems(): ExtractedItem[] {
    const items: ExtractedItem[] = []
    // Yahoo Auction 用セレクタ（実装）
    return items
  },
}

export const YahooFleaParser = {
  isListPage(): boolean {
    return /flea\.yahoo\.co\.jp\/search/.test(window.location.href)
  },

  extractItems(): ExtractedItem[] {
    const items: ExtractedItem[] = []
    // Yahoo Flea 用セレクタ（実装）
    return items
  },
}
