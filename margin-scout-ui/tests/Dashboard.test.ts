import { describe, it, expect, beforeEach, vi } from "vitest"
import { mount } from "@vue/test-utils"
import SavedItems from "../src/views/Dashboard/SavedItems.vue"
import { capturesAPI } from "../src/services/api"

vi.mock("../src/services/api", () => {
  return {
    capturesAPI: {
      getSavedItems: vi.fn(),
      exportSavedItemsCSV: vi.fn(),
    }
  }
})

describe("SavedItems.vue", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("displays saved items list", async () => {
    const mockItems = [
      {
        id: "1",
        title: "iPhone 14",
        source: "mercari",
        source_price_jpy: 95000,
        url: "https://mercari.jp/item/m1",
        profit_jpy: 50000,
        profit_margin_pct: 52.6,
        created_at: "2026-06-17T10:30:00Z",
      },
    ]

    vi.mocked(capturesAPI.getSavedItems).mockResolvedValue({
      data: { items: mockItems, total: 1 },
    } as any)

    const wrapper = mount(SavedItems)
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick() // Wait for promises to resolve

    expect(wrapper.text()).toContain("iPhone 14")
    expect(wrapper.text()).toContain("¥95,000")
  })

  it("exports selected items as CSV", async () => {
    const mockBlob = new Blob(["商品名,ソース\niPhone,mercari\n"])
    vi.mocked(capturesAPI.exportSavedItemsCSV).mockResolvedValue({
      data: mockBlob,
    } as any)

    const wrapper = mount(SavedItems)
    wrapper.vm.selectedItems = ["1", "2"]
    
    // mock global.window.URL
    const createObjectURL = vi.fn().mockReturnValue("blob:test")
    const revokeObjectURL = vi.fn()
    global.window.URL.createObjectURL = createObjectURL
    global.window.URL.revokeObjectURL = revokeObjectURL

    await wrapper.vm.exportCSV()

    expect(capturesAPI.exportSavedItemsCSV).toHaveBeenCalledWith(["1", "2"])
    expect(createObjectURL).toHaveBeenCalled()
  })

  it("filters items by source", async () => {
    vi.mocked(capturesAPI.getSavedItems).mockResolvedValue({
      data: { items: [], total: 0 },
    } as any)

    const wrapper = mount(SavedItems)
    await wrapper.vm.$nextTick()

    wrapper.vm.filterSource = "mercari"
    await wrapper.vm.$nextTick()

    expect(capturesAPI.getSavedItems).toHaveBeenCalled()
  })
})
