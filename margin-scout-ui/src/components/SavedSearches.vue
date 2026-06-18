<template>
  <div class="saved-searches-container">
    <div class="header">
      <h2>保存済み検索</h2>
      <button @click="showCreateModal = true" class="btn btn-primary">
        + 新規検索を保存
      </button>
    </div>

    <div v-if="loading" class="loading">読み込み中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="searches.length === 0" class="empty-state">
      <p>保存済み検索はまだありません。</p>
    </div>

    <table v-else class="searches-table">
      <thead>
        <tr>
          <th>名前</th>
          <th>ソース</th>
          <th>監視中</th>
          <th>最終実行</th>
          <th>ステータス</th>
          <th>アクション</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="search in searches" :key="search.id">
          <td>{{ search.name }}</td>
          <td>{{ sourceLabel(search.source) }}</td>
          <td>
            <span v-if="search.is_monitoring_enabled" class="badge badge-success">
              有効
            </span>
            <span v-else class="badge badge-secondary">無効</span>
          </td>
          <td>{{ formatDate(search.last_run_at) }}</td>
          <td>
            <span :class="['status', `status-${search.last_run_status}`]">
              {{ statusLabel(search.last_run_status) }}
            </span>
          </td>
          <td>
            <button @click="handleRerun(search.id)" class="btn btn-sm btn-secondary">
              再実行
            </button>
            <button @click="handleEdit(search.id)" class="btn btn-sm btn-secondary">
              編集
            </button>
            <button @click="handleDelete(search.id)" class="btn btn-sm btn-danger">
              削除
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Create/Edit Modal -->
    <SavedSearchModal
      v-if="showCreateModal"
      :search="editingSearch"
      @save="handleSave"
      @close="showCreateModal = false; editingSearch = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useSavedSearchStore } from "../stores/savedSearchStore";
import SavedSearchModal from "./SavedSearchModal.vue";

const store = useSavedSearchStore();
const { searches, loading, error } = storeToRefs(store);

const showCreateModal = ref(false);
const editingSearch = ref<any>(null);

onMounted(() => {
  store.fetchSearches();
});

const sourceLabel = (source: string) => ({
  mercari: "メルカリ",
  yahoo_auction: "Yahoo!オークション",
  yahoo_flea: "Yahoo!フリマ",
}[source] || source);

const statusLabel = (status: string | null) => ({
  pending: "保留中",
  success: "成功",
  failed: "失敗",
  null: "-",
}[status || "null"] || "-");

const formatDate = (date: string | null) => {
  if (!date) return "-";
  return new Date(date).toLocaleString("ja-JP");
};

const handleRerun = async (id: string) => {
  await store.rerunSearch(id);
  alert("再実行しました");
  store.fetchSearches();
};

const handleEdit = (id: string) => {
  editingSearch.value = searches.value.find((s) => s.id === id) || null;
  showCreateModal.value = true;
};

const handleDelete = async (id: string) => {
  if (confirm("この検索を削除してもよろしいですか？")) {
    await store.deleteSearch(id);
  }
};

const handleSave = async (data: any) => {
  if (editingSearch.value?.id) {
    await store.updateSearch(editingSearch.value.id, data);
  } else {
    await store.createSearch(data);
  }
  showCreateModal.value = false;
  editingSearch.value = null;
};
</script>

<style scoped>
.saved-searches-container {
  padding: 1.5rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.searches-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.searches-table th,
.searches-table td {
  border: 1px solid #ddd;
  padding: 0.75rem;
  text-align: left;
}

.searches-table th {
  background-color: #f5f5f5;
  font-weight: 600;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.badge-success {
  background-color: #d4edda;
  color: #155724;
}

.badge-secondary {
  background-color: #e2e3e5;
  color: #383d41;
}

.status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.status-success {
  background-color: #d4edda;
  color: #155724;
}

.status-failed {
  background-color: #f8d7da;
  color: #721c24;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
}

.btn {
  padding: 0.5rem 1rem;
  margin: 0 0.25rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.loading,
.error,
.empty-state {
  text-align: center;
  padding: 2rem;
}

.error {
  color: #dc3545;
}
</style>
