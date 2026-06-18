import { defineStore } from 'pinia';
import { savedSearchAPI } from '../services/api';
import { ref } from 'vue';

export interface SavedSearch {
  id: string;
  name: string;
  source: "mercari" | "yahoo_auction" | "yahoo_flea";
  filters: Record<string, any>;
  is_monitoring_enabled: boolean;
  monitoring_interval_hours: number;
  next_run_at: string;
  last_run_at: string | null;
  last_run_status: "pending" | "success" | "failed" | null;
  last_run_error: string | null;
  created_at: string;
}

export const useSavedSearchStore = defineStore('savedSearch', () => {
  const searches = ref<SavedSearch[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchSearches = async (limit = 20, offset = 0) => {
    loading.value = true;
    error.value = null;
    try {
      const res = await savedSearchAPI.list(limit, offset);
      // Backend returns either list directly or dict with searches key
      searches.value = Array.isArray(res.data) ? res.data : res.data.searches || [];
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to fetch searches";
    } finally {
      loading.value = false;
    }
  };

  const getSearch = async (id: string) => {
    const res = await savedSearchAPI.get(id);
    return res.data as SavedSearch;
  };

  const createSearch = async (data: Partial<SavedSearch>) => {
    const res = await savedSearchAPI.create(data as any);
    searches.value.push(res.data);
    return res.data as SavedSearch;
  };

  const updateSearch = async (id: string, data: Partial<SavedSearch>) => {
    const res = await savedSearchAPI.update(id, data as any);
    const index = searches.value.findIndex(s => s.id === id);
    if (index !== -1) {
      searches.value[index] = res.data;
    }
    return res.data as SavedSearch;
  };

  const deleteSearch = async (id: string) => {
    await savedSearchAPI.delete(id);
    searches.value = searches.value.filter(s => s.id !== id);
  };

  const rerunSearch = async (id: string) => {
    const res = await savedSearchAPI.rerun(id);
    return res.data;
  };

  const disableMonitoring = async (id: string) => {
    await savedSearchAPI.disableMonitoring(id);
    const index = searches.value.findIndex(s => s.id === id);
    if (index !== -1) {
      searches.value[index].is_monitoring_enabled = false;
    }
  };

  return {
    searches,
    loading,
    error,
    fetchSearches,
    getSearch,
    createSearch,
    updateSearch,
    deleteSearch,
    rerunSearch,
    disableMonitoring
  };
});
