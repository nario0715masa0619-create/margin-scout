# MarginScout Dashboard Search UI 仕様書 v2

## 1. 概要
本仕様書は、リサーチ条件設定ダッシュボードにおける検索オプションおよび商品コンディションの複数選択（チェックボックス）対応に関する、フロントエンド（UI/State）、API連携、バックエンド（DTO）の統合仕様を定義します。

## 2. UI仕様の更新
既存のダッシュボードに対して、検索オプション（4項目）およびコンディション（6項目）を複数選択可能なチェックボックスグループとして追加します。

### 2.1 検索オプション（4項目）
- **`on_sale`**：販売中
- **`sold_out`**：売り切れ
- **`fixed_price`**：通常出品（即決）
- **`auction`**：オークション

### 2.2 コンディション（6項目）
- **`new`**：新品、未使用
- **`almost_new`**：未使用に近い
- **`no_scratches`**：目立った傷や汚れなし
- **`slight_scratches`**：やや傷や汚れあり
- **`scratched`**：傷や汚れあり
- **`bad_condition`**：全体的に状態が悪い

## 3. Frontend 仕様

### 3.1 State 管理
`S01_ResearchStart.vue` および関連する Pinia store において、以下の状態を追加・管理します。
- `selected_options`: `string[]` (初期値: `[]` または全選択)
- `selected_conditions`: `string[]` (初期値: `[]` または全選択)

### 3.2 TypeScript 型定義スニペット
`margin-scout-ui/src/types/research.d.ts` (または既存の型定義ファイル) に追加・更新します。

```typescript
export type SearchOption = 'on_sale' | 'sold_out' | 'fixed_price' | 'auction';
export type ItemCondition = 'new' | 'almost_new' | 'no_scratches' | 'slight_scratches' | 'scratched' | 'bad_condition';

export interface ResearchConditions {
  keywords: string[];
  sources: string[];
  days_back: number;
  min_sales: number;
  selected_options: SearchOption[];
  selected_conditions: ItemCondition[];
}

export interface ResearchStartPayload {
  title: string;
  conditions: ResearchConditions;
}
```

### 3.3 Vue コンポーネント修正スニペット (`S01_ResearchStart.vue`)
template 内にチェックボックスグループを追加し、`v-model` で配列にバインドします。

```vue
<!-- S01_ResearchStart.vue の template 追記部分 -->
<div class="form-group">
  <label>検索オプション（複数選択可）</label>
  <div class="checkbox-group">
    <label class="checkbox-label">
      <input type="checkbox" value="on_sale" v-model="selectedOptions" /> 販売中
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="sold_out" v-model="selectedOptions" /> 売り切れ
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="fixed_price" v-model="selectedOptions" /> 通常出品
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="auction" v-model="selectedOptions" /> オークション
    </label>
  </div>
</div>

<div class="form-group">
  <label>コンディション（複数選択可）</label>
  <div class="checkbox-group">
    <label class="checkbox-label">
      <input type="checkbox" value="new" v-model="selectedConditions" /> 新品、未使用
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="almost_new" v-model="selectedConditions" /> 未使用に近い
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="no_scratches" v-model="selectedConditions" /> 目立った傷や汚れなし
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="slight_scratches" v-model="selectedConditions" /> やや傷や汚れあり
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="scratched" v-model="selectedConditions" /> 傷や汚れあり
    </label>
    <label class="checkbox-label">
      <input type="checkbox" value="bad_condition" v-model="selectedConditions" /> 全体的に状態が悪い
    </label>
  </div>
</div>
```

```typescript
// script setup 追記部分
const selectedOptions = ref<string[]>(['on_sale', 'fixed_price']);
const selectedConditions = ref<string[]>(['new', 'almost_new', 'no_scratches']);

// startResearch メソッド内ペイロード修正
const response = await researchAPI.startResearch({
  title: "Untitled Research",
  conditions: {
    keywords: keywordList,
    sources: selectedSources.value,
    days_back: daysBack.value,
    min_sales: minSales.value,
    selected_options: selectedOptions.value,
    selected_conditions: selectedConditions.value
  }
});
```

## 4. API & Backend 仕様

### 4.1 API リクエスト
- **Endpoint**: `POST /api/v1/research-jobs/`
- **Payload**: 上記 `ResearchStartPayload` に準拠。

### 4.2 Pydantic DTO スニペット
`margin-scout-backend/app/schemas/research_job.py` に Enum 定義とリスト型のバリデーションを追加します。

```python
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchOptionEnum(str, Enum):
    on_sale = "on_sale"
    sold_out = "sold_out"
    fixed_price = "fixed_price"
    auction = "auction"

class ItemConditionEnum(str, Enum):
    new = "new"
    almost_new = "almost_new"
    no_scratches = "no_scratches"
    slight_scratches = "slight_scratches"
    scratched = "scratched"
    bad_condition = "bad_condition"

class JobConditions(BaseModel):
    keywords: List[str]
    sources: List[str]
    days_back: int
    min_sales: int
    selected_options: List[SearchOptionEnum] = Field(default_factory=list)
    selected_conditions: List[ItemConditionEnum] = Field(default_factory=list)

# 既存の JobRequest の conditions の型をより厳密にする場合は以下のように修正
class JobRequest(BaseModel):
    title: Optional[str] = "Untitled Research"
    conditions: JobConditions = Field(..., description="検索条件")
```
> [!NOTE]
> `conditions` を `Dict[str, Any]` から厳密な Pydantic モデル (`JobConditions`) に変更することで、バリデーションと型ヒントが強化されます。

## 5. 受け入れ条件 (Acceptance Criteria)

1. **UI**: 検索オプションとコンディションのチェックボックスが正しく表示され、複数選択・解除が正常に動作すること。
2. **State**: 選択状態が配列として `selectedOptions`, `selectedConditions` に保持され、Pinia storeへ正しく保存されること。
3. **API**: リサーチ開始時に、APIペイロードの `conditions` オブジェクト内に配列が正しく含まれて送信されること。
4. **Backend**: 
   - `selected_options` および `selected_conditions` が Pydantic のバリデーション（Enum値チェック含む）を通過すること。
   - 不正な値が送信された場合は `422 Unprocessable Entity` を返すこと。
   - DBの `conditions` JSONカラムに配列データが正しく格納されること。
5. **E2E Test**: 
   - 複数オプションを選択してリサーチを実行し、モニタリング画面へ遷移する一連のフローが成功すること。
