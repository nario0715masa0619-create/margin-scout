// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import SavedSearches from "../src/components/SavedSearches.vue";
import * as api from "../src/services/api";

vi.mock("../src/services/api", () => {
  return {
    savedSearchAPI: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      rerun: vi.fn(),
      disableMonitoring: vi.fn(),
    }
  };
});

describe("SavedSearches.vue", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("renders saved searches list", async () => {
    const mockSearches = [
      {
        id: "1",
        name: "iPhone検索",
        source: "mercari",
        is_monitoring_enabled: true,
        last_run_status: "success",
      },
    ];

    vi.mocked(api.savedSearchAPI.list).mockResolvedValue({
      data: { searches: mockSearches },
    });

    const wrapper = mount(SavedSearches);
    
    // Wait for the fetch operation to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("iPhone検索");
  });

  it("opens create modal on button click", async () => {
    vi.mocked(api.savedSearchAPI.list).mockResolvedValue({
      data: { searches: [] },
    });

    const wrapper = mount(SavedSearches);
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    await wrapper.find(".btn-primary").trigger("click");
    expect(wrapper.find(".modal-overlay").exists()).toBe(true);
  });

  it("handles rerun action", async () => {
    const mockSearches = [
      {
        id: "1",
        name: "iPhone検索",
        source: "mercari",
        is_monitoring_enabled: true,
        last_run_status: "success",
      },
    ];

    vi.mocked(api.savedSearchAPI.list).mockResolvedValue({
      data: { searches: mockSearches },
    });
    vi.mocked(api.savedSearchAPI.rerun).mockResolvedValue({ data: {} });
    
    // Mock window.alert
    const alertMock = vi.fn();
    vi.stubGlobal('alert', alertMock);

    const wrapper = mount(SavedSearches);
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    const buttons = wrapper.findAll(".btn-secondary");
    // The first secondary button is "再実行" (Rerun)
    await buttons[0].trigger("click");
    
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    expect(api.savedSearchAPI.rerun).toHaveBeenCalledWith("1");
    expect(alertMock).toHaveBeenCalledWith("再実行しました");
    
    vi.unstubAllGlobals();
  });
});
