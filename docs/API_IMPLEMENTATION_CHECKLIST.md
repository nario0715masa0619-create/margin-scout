# API 実装チェックリスト

## Backend API (FastAPI)

### ✅ 実装済み
- [x] POST /api/research/jobs - リサーチ開始
- [x] GET /api/research/jobs/{job_id} - ジョブ状態取得
- [x] GET /api/research/jobs/{job_id}/results - 候補一覧取得
- [x] GET /api/research/jobs/{job_id}/results/{candidate_id} - 詳細取得
- [x] POST /api/research/jobs/{job_id}/export/csv - CSV エクスポート
- [x] POST /api/research/jobs/{job_id}/cancel - ジョブキャンセル
- [x] GET /api/research/jobs/{job_id}/logs/summary - ログサマリー取得

### ⏳ 未実装（今後）
- [ ] GET /api/research/jobs - ジョブ一覧取得
- [ ] DELETE /api/research/jobs/{job_id} - ジョブ削除
- [ ] PUT /api/research/jobs/{job_id} - ジョブ編集

---

## Frontend API 連携 (Vue 3 + Axios)

### S01: リサーチ条件設定

**実装項目**:
- [ ] フォーム入力値の取得
- [ ] バリデーション（キーワード、ソース）
- [ ] POST /api/research/jobs API 呼び出し
- [ ] job_id を Pinia ストアに保存
- [ ] S02 へ遷移（job_id をパラメータ付き）
- [ ] エラー時: エラーモーダル表示 + 再試行

**コード例**:
```typescript
import { researchAPI } from '../services/api'

const startResearch = async () => {
  try {
    const response = await researchAPI.startResearch({
      keywords: keywords.value.split(',').map(k => k.trim()),
      sources: selectedSources.value,
      days_back: daysBack.value,
      min_sales: minSales.value
    })
    
    store.setJobState({
      jobId: response.job_id,
      status: 'running'
    })
    
    router.push({ 
      name: 'ExecutionMonitor', 
      params: { jobId: response.job_id } 
    })
  } catch (err) {
    error.value = err.message
    showErrorModal.value = true
  }
}
```

---

### S02: 実行中モニター

**実装項目**:
- [ ] ジョブ状態定期取得（2秒間隔、10分 timeout）
- [ ] GET /api/research/jobs/{job_id} ポーリング
- [ ] 進捗バー更新（progress 属性）
- [ ] 取得件数・マッチ件数リアルタイム更新
- [ ] status が "completed" で S03 自動遷移
- [ ] status が "failed" でエラーモーダル表示
- [ ] キャンセルボタン → POST /api/research/jobs/{job_id}/cancel

**ポーリング実装例**:
```typescript
import { ref, onMounted, onUnmounted } from 'vue'

const pollInterval = ref<number | null>(null)

const fetchJobStatus = async () => {
  try {
    const data = await researchAPI.getJobStatus(jobId.value)
    
    store.setJobState({
      jobId: data.job_id,
      status: data.status,
      progress: data.progress,
      totalItems: data.total_items,
      matchedItems: data.matched_items
    })
    
    if (data.status === 'completed') {
      clearInterval(pollInterval.value!)
      router.push({ name: 'CandidateList', params: { jobId: jobId.value } })
    }
  } catch (err) {
    statusMessage.value = { type: 'error', text: err.message }
  }
}

onMounted(() => {
  fetchJobStatus()
  pollInterval.value = window.setInterval(fetchJobStatus, 2000)
})

onUnmounted(() => {
  if (pollInterval.value) clearInterval(pollInterval.value)
})
```

---

### S03: 候補一覧

**実装項目**:
- [ ] GET /api/research/jobs/{job_id}/results API 呼び出し
- [ ] 結果をテーブルに表示
- [ ] チェックボックス選択 → Pinia selectedCandidates に追加
- [ ] ソート機能（利益順、スコア順）
- [ ] フィルター機能（商品名検索）
- [ ] 全選択・選択解除ボタン
- [ ] 商品名クリック → S04 遷移（candidateId 付き）
- [ ] CSV出力ボタン（選択件数表示）

**テーブル実装例**:
```typescript
const filteredCandidates = computed(() => {
  let filtered = candidates.value.filter(c =>
    c.product_name.toLowerCase().includes(searchText.value.toLowerCase())
  )
  
  if (sortBy.value === 'profit_desc') {
    filtered.sort((a, b) => b.profit_jpy - a.profit_jpy)
  } else if (sortBy.value === 'profit_asc') {
    filtered.sort((a, b) => a.profit_jpy - b.profit_jpy)
  }
  
  return filtered
})

const toggleSelectedCandidate = (candidateId: string) => {
  store.toggleSelectedCandidate(candidateId)
}
```

---

### S04: 候補詳細

**実装項目**:
- [ ] GET /api/research/jobs/{job_id}/results/{candidate_id} API 呼び出し
- [ ] 詳細情報を複数セクションに表示
- [ ] 前後ナビゲーション（◀ 前 / 次 ▶）
- [ ] 選択チェック（既に選択済みの場合は「✓ 選択済み」）
- [ ] 選択/未選択の切り替え
- [ ] URL リンク生成（Mercari/Yahoo へのリンク）

**詳細取得例**:
```typescript
const fetchCandidateDetail = async () => {
  try {
    const data = await researchAPI.getCandidateDetail(
      jobId.value, 
      candidateId.value
    )
    candidate.value = data
  } catch (err) {
    console.error(err)
  }
}
```

---

### S05: CSV出力

**実装項目**:
- [ ] 出力オプション選択（利益率、URL 含有）
- [ ] 出力列プレビュー表示
- [ ] POST /api/research/jobs/{job_id}/export/csv API 呼び出し
- [ ] CSV ファイルダウンロード処理
- [ ] 完了メッセージ表示（ファイル名）

**CSV ダウンロード実装例**:
```typescript
const downloadCsv = async () => {
  try {
    const response = await researchAPI.exportCsv(jobId.value)
    
    // CSV データ生成（Backend から HTML 返却の場合）
    const csvData = generateCsvContent(store.selectedCandidates)
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `research_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    message.value = { type: 'success', text: 'CSV をダウンロードしました' }
  } catch (err) {
    message.value = { type: 'error', text: err.message }
  }
}
```

---

## エラーハンドリング

### 共通エラー処理

```typescript
// src/services/api.ts に interceptor 追加
api.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') {
      // タイムアウト
      return Promise.reject(new Error('リクエストがタイムアウトしました'))
    } else if (error.response?.status === 404) {
      // ジョブ未検出
      return Promise.reject(new Error('ジョブが見つかりません'))
    } else if (error.response?.status >= 500) {
      // サーバーエラー
      return Promise.reject(new Error('サーバーエラーが発生しました。しばらく後にお試しください'))
    }
    return Promise.reject(error)
  }
)
```

### 各画面のエラー表示方法

| 画面 | エラー表示 | 再試行可否 |
|------|--------|---------|
| S01 | インライン通知 | ○ |
| S02 | モーダル + ログパネル | ○ |
| S03 | トースト通知 | ○ |
| S04 | インライン通知 | ○ |
| S05 | モーダル | ○ |

---

## テスト手順

### 手動テスト（QA 用）

#### S01 テスト
```
1. キーワード空 → 「キーワードを入力してください」エラー表示 ✓
2. キーワード入力 + ソース選択 → ボタン有効化 ✓
3. 「リサーチ開始」クリック → S02 へ遷移 ✓
4. Swagger UI で job_id 確認 ✓
```

#### S02 テスト
```
1. 進捗バー 0% 表示 ✓
2. 2 秒ごとに status 更新 ✓
3. 取得件数・マッチ件数リアルタイム更新 ✓
4. status: completed → S03 自動遷移 ✓
5. キャンセルボタンクリック → ジョブキャンセル ✓
```

#### S03 テスト
```
1. テーブルに 12 件表示 ✓
2. 商品名検索で フィルター ✓
3. ソートボタンで利益順・スコア順 ✓
4. チェックボックス選択 → Pinia に反映 ✓
5. 商品名クリック → S04 遷移 ✓
```

#### S04 テスト
```
1. 詳細情報すべて表示 ✓
2. ◀ 前 / 次 ▶ ナビゲーション動作 ✓
3. ✓ 選択ボタンで on/off 切り替え ✓
4. URL リンク外部サイトに遷移 ✓
```

#### S05 テスト
```
1. 出力オプション選択 → 列プレビュー更新 ✓
2. CSV ダウンロードボタン → ファイル保存 ✓
3. CSV 内容確認（列 + 行数一致） ✓
4. 完了メッセージ表示 ✓
```

---

## デバッグ チェックリスト

- [ ] ブラウザコンソールに TypeScript エラーなし
- [ ] Network タブで API レスポンス確認
- [ ] Pinia DevTools で store 状態確認
- [ ] Vue DevTools で コンポーネント構造確認
- [ ] Chrome DevTools で CSS 確認

---
