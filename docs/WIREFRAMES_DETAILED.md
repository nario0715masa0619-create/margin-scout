# MarginScout UI ワイヤーフレーム詳細版

## S01: リサーチ条件設定

### レイアウト構成
```
┌─────────────────────────────────────────────┐
│ Header (60px)                               │
│ MarginScout v2.1 | [Home] [Research]        │
├─────────────────────────────────────────────┤
│                                             │
│  Container (max-width: 800px)               │
│                                             │
│    Section 1: フォーム (600px)               │
│    ┌─────────────────────────────────────┐ │
│    │                                     │ │
│    │ 📋 リサーチ条件設定                  │ │
│    │                                     │ │
│    │ 【キーワード】                      │ │
│    │ Label: "キーワード (カンマ区切り)"  │ │
│    │ Input: placeholder="iPhone, Canon" │ │
│    │ Hint: "複数キーワードはカンマで区切り" │
│    │                                     │ │
│    │ 【取得元】                          │ │
│    │ ☑ Mercari (mercari)               │ │
│    │ ☑ Yahoo Flea Market (yahoo_flea)  │ │
│    │ ☑ Yahoo Auction (yahoo_auction)   │ │
│    │ ☑ Hardoff (hardoff)               │ │
│    │ Hint: "複数選択可能"                │ │
│    │                                     │ │
│    │ 【オプション】                      │ │
│    │ 取得対象期間: [90] 日               │ │
│    │ 最小販売数: [2] 件                   │ │
│    │                                     │ │
│    │ [Button: 🚀 リサーチ開始]           │ │
│    │ (disabled if: !keywords || !sources) │ │
│    │                                     │ │
│    │ 【エラー表示】                      │ │
│    │ ⚠️  キーワードを入力してください     │ │
│    │ (bg: #f8d7da, color: #721c24)      │ │
│    │                                     │ │
│    └─────────────────────────────────────┘ │
│                                             │
│  Footer (60px)                              │
│  &copy; 2026 MarginScout. All rights...     │
│                                             │
└─────────────────────────────────────────────┘
```

### CSS Grid/Flex 構成
```
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

label { font-weight: 600; margin-bottom: 0.25rem; }
input, textarea { padding: 0.5rem; border: 1px solid #ccc; }
input:disabled { background: #f5f5f5; color: #999; }

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}
```

---

## S02: 実行中モニター

### レイアウト構成
```
┌─────────────────────────────────────────────┐
│ Header                                      │
├─────────────────────────────────────────────┤
│                                             │
│  Container                                  │
│                                             │
│    ⚙️  実行中モニター                        │
│                                             │
│    Job Info Box (bg: #e3f2fd)               │
│    ジョブID: 550e8400-e29b-41d4-a716...    │
│    状態: 実行中                             │
│    進捗: 45%                                │
│                                             │
│    Progress Bar (h: 30px)                   │
│    ████████░░░░░░░░░░░░ 45%                │
│    (bg: #ddd, fill: linear-gradient)       │
│                                             │
│    Stats Grid (2x2)                         │
│    ┌─────────────┬─────────────┐           │
│    │ 取得件数    │ マッチ件数   │           │
│    │     20      │     12      │           │
│    └─────────────┴─────────────┘           │
│                                             │
│    Actions                                  │
│    [キャンセル (enabled)]                  │
│    [候補一覧へ (disabled)]                  │
│                                             │
│    Status Message (if any)                  │
│    ✓ リサーチが完了しました！                │
│    (bg: #d4edda, color: #155724)           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## S03: 候補一覧

### テーブルコンポーネント
```
┌─────────────────────────────────────────────────┐
│ Filter/Action Bar                               │
│ [🔍 検索: ________] [▼ ソート] [全選択] [解除] │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑│ 商品名        │ 取得元  │ 仕入  │ ... │ │
│ ├─────────────────────────────────────────────┤ │
│ │ ☑│ iPhone 16 Pro │ mercari │ ¥80k │ ... │ │
│ │ ☐│ Canon EOS 5D  │ yahoo   │ ¥16k │ ... │ │
│ │ ☑│ Gucci Bag     │ mercari │ ¥20k │ ... │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [📥 CSV出力 (選択3件)]                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 行の状態

```
Normal: background: white
Hover:  background: #f9f9f9; cursor: pointer
Selected: チェック ☑ 状態
Loss:    background: #fff5f5 (利益 < 0)
```

---

## S04: 候補詳細

### レイアウト構成
```
┌─────────────────────────────────────────────┐
│ Header                                      │
├─────────────────────────────────────────────┤
│                                             │
│  Container (max: 800px)                     │
│                                             │
│    Section 1: 基本情報                      │
│    商品名: iPhone 16 Pro Max                │
│    取得元: Mercari                          │
│    条件: Used - Like New                    │
│                                             │
│    Section 2: 価格比較 (bg: #f9f9f9)       │
│    ┌──────┐    ┌──────┐                   │
│    │ 仕入 │ → │ eBay │                   │
│    │ ¥80k │    │ $1.2k│                   │
│    └──────┘    └──────┘                   │
│                                             │
│    Section 3: 利益計算 (grid 2x2)          │
│    ┌────────┬────────┐                    │
│    │ 利益   │ 利益率 │                    │
│    │¥25,000 │ 31.25% │                    │
│    │ スコア │ ステータス                   │
│    │ 0.89   │ success│                    │
│    └────────┴────────┘                    │
│                                             │
│    Section 4: eBay情報                     │
│    eBay商品: [eBay] iPhone 16 Pro Max     │
│    Item ID: 395123456789                   │
│                                             │
│    Navigation & Actions                    │
│    [◀ 前] [✓ 選択] [次 ▶] [戻る]          │
│                                             │
└─────────────────────────────────────────────┘
```

---

## S05: CSV出力

### レイアウト構成
```
┌─────────────────────────────────────────────┐
│ Header                                      │
├─────────────────────────────────────────────┤
│                                             │
│  Container                                  │
│                                             │
│    💾 CSV出力                                │
│                                             │
│    【出力情報】                              │
│    ジョブID: 550e8400-e29b-41d4-a716...    │
│    出力件数: 12 件                          │
│                                             │
│    【オプション】                            │
│    ☑ 利益率を含める                        │
│    ☑ URL を含める                          │
│    ☐ 黒字のみ出力                          │
│                                             │
│    【出力列プレビュー】                      │
│    [candidate_id] [product_name]          │
│    [source_channel] [source_price_jpy]    │
│    [ebay_title] [ebay_price_usd]          │
│    [profit_jpy] [profit_margin_pct]       │
│    [source_url]                           │
│                                             │
│    [📥 CSV ダウンロード] [戻る]            │
│                                             │
│    【完了メッセージ】                        │
│    ✓ 出力成功 (research_results_20260615.csv) │
│    (bg: #d4edda, color: #155724)           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 共通要素

### ナビゲーションバー
```
Height: 60px
Background: #2c3e50
Color: white

Layout:
├─ Logo/Brand (left): "MarginScout v2.1"
└─ Nav Links (right): [Home] [Research]

Links:
- Home (/) → リセット状態
- Research (/research) → S01 へ
```

### フッター
```
Height: 60px
Background: #2c3e50
Color: white

Content: "&copy; 2026 MarginScout. All rights reserved."
```

---

## デバイス対応

| デバイス | 幅 | 対応 | 備考 |
|---------|----|----|------|
| スマートフォン | 320-767px | ✗ | 未対応 |
| タブレット | 768-1023px | ✗ | 未対応 |
| デスクトップ | 1024px+ | ✓ | 対応 |

---
