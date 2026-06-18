import { describe, it, expect, beforeEach } from "vitest"
import { MercariParser } from "~services/dom-parser"

describe("MercariParser", () => {
  beforeEach(() => {
    // DOM をリセット
    document.body.innerHTML = ""
    Object.defineProperty(window, "location", {
      value: {
        href: "https://mercari.jp/search?keyword=iPhone",
        origin: "https://mercari.jp"
      },
      writable: true,
    })
  })

  it("should detect Mercari search page", () => {
    expect(MercariParser.isListPage()).toBe(true)
  })

  it("should extract items from product cards", () => {
    // Mock HTML
    document.body.innerHTML = `
      <div data-testid="product-card-anchor" href="/item/m12345">
        <h2>iPhone 14 Pro</h2>
        <span class="price">¥95,000</span>
        <img src="https://example.com/item.jpg" />
      </div>
    `

    const items = MercariParser.extractItems()
    expect(items).toHaveLength(1)
    expect(items[0].title).toBe("iPhone 14 Pro")
    expect(items[0].price_jpy).toBe(95000)
  })
})
