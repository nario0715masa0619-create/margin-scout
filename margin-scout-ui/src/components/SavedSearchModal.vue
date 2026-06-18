<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ search ? "検索を編集" : "新規検索を保存" }}</h3>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-body">
        <div class="form-group">
          <label>検索名 *</label>
          <input v-model="form.name" type="text" required />
        </div>

        <div class="form-group">
          <label>ソース *</label>
          <select v-model="form.source" required>
            <option value="">-- 選択 --</option>
            <option value="mercari">メルカリ</option>
            <option value="yahoo_auction">Yahoo!オークション</option>
            <option value="yahoo_flea">Yahoo!フリマ</option>
          </select>
        </div>

        <fieldset class="filters-fieldset">
          <legend>フィルター設定</legend>

          <div class="form-group">
            <label>キーワード *</label>
            <input v-model="form.filters.keyword" type="text" required />
          </div>

          <div class="form-group">
            <label>最低価格 (円)</label>
            <input v-model.number="form.filters.price_range.min" type="number" />
          </div>

          <div class="form-group">
            <label>最高価格 (円)</label>
            <input v-model.number="form.filters.price_range.max" type="number" />
          </div>

          <div class="form-group">
            <label>条件</label>
            <select v-model="form.filters.conditions" multiple>
              <option value="new">新品</option>
              <option value="used">中古</option>
            </select>
          </div>

          <div class="form-group">
            <label>ソート</label>
            <select v-model="form.filters.sort">
              <option value="newest">新着順</option>
              <option value="price_asc">安い順</option>
              <option value="price_desc">高い順</option>
              <option value="profit_desc">利益が高い順</option>
            </select>
          </div>

          <div class="form-group">
            <label>除外キーワード</label>
            <input v-model="form.filters.exclude_keywords" type="text" placeholder="複数の場合はカンマ区切り" />
          </div>
        </fieldset>

        <fieldset class="monitoring-fieldset">
          <legend>監視設定</legend>

          <div class="form-group">
            <label>
              <input v-model="form.is_monitoring_enabled" type="checkbox" />
              自動監視を有効にする
            </label>
          </div>

          <div v-if="form.is_monitoring_enabled" class="form-group">
            <label>監視間隔 (時間) *</label>
            <input v-model.number="form.monitoring_interval_hours" type="number" min="1" required />
          </div>
        </fieldset>

        <div class="modal-footer">
          <button type="button" @click="$emit('close')" class="btn btn-secondary">
            キャンセル
          </button>
          <button type="submit" class="btn btn-primary">
            {{ search ? "更新" : "保存" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

interface Props {
  search?: any;
}

const props = defineProps<Props>();
const emit = defineEmits<{ save: [data: any]; close: [] }>();

const form = ref({
  name: "",
  source: "",
  filters: {
    keyword: "",
    price_range: { min: null as number | null, max: null as number | null },
    conditions: [] as string[],
    sort: "newest",
    exclude_keywords: "",
  },
  is_monitoring_enabled: false,
  monitoring_interval_hours: 24,
});

watch(
  () => props.search,
  (newSearch) => {
    if (newSearch) {
      form.value = JSON.parse(JSON.stringify(newSearch));
    } else {
      form.value = {
        name: "",
        source: "",
        filters: {
          keyword: "",
          price_range: { min: null, max: null },
          conditions: [],
          sort: "newest",
          exclude_keywords: "",
        },
        is_monitoring_enabled: false,
        monitoring_interval_hours: 24,
      };
    }
  },
  { immediate: true }
);

const handleSubmit = () => {
  emit("save", form.value);
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #ddd;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group select[multiple] {
  height: auto;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

.filters-fieldset,
.monitoring-fieldset {
  margin: 1.5rem 0;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filters-fieldset legend,
.monitoring-fieldset legend {
  padding: 0 0.5rem;
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1.5rem;
  border-top: 1px solid #ddd;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}
</style>
