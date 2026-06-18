# Browser Extension Specification

## 1. 概要
MarginScout の主軸となるデータ抽出コンポーネントである Browser Extension (Chrome 拡張機能) の仕様です。
SaaS バックエンドへの重いスクレイピング負荷をオフロードし、ユーザーのブラウザ上で安全に DOM 解析を行います。

## 2. 権限とスコープ (Manifest V3)
- `permissions`:
  - `storage` (SaaS からの JWT トークンや検索設定の保存)
  - `activeTab`, `scripting` (フリマサイトへの Content Script の注入と DOM 操作)
- `host_permissions`:
  - `https://*.mercari.com/*`
  - `https://*.yahoo.co.jp/*`
  - SaaS Backend の API ドメイン (`https://api.marginscout.com/*` など)

## 3. コンポーネント構成

### 3.1 Popup (UI)
- SaaS ダッシュボードへのログイン状態の表示。
- 現在のページでの「MarginScout 抽出実行」ボタン。
- 利益計算結果の簡易サマリー表示。
- SaaS Dashboard へのリンク導線。

### 3.2 Content Scripts (Data Extractor)
- 対象サイト（メルカリ、ヤフオク等）の検索結果一覧ページに注入されます。
- `document.querySelectorAll` や `element.innerText` を用いて、商品タイトル、価格、URL などを抽出します。
- 抽出ロジックは対象サイトごとに分離（Adapter パターンライク）して管理します。
- **UI インジェクション**: 抽出・計算後、可能であれば各商品カードの上に「見込み利益: ¥1,500」などのバッジ（HTML 要素）を直接挿入し、ユーザーの直感的なリサーチを支援します。

### 3.3 Background Service Worker
- Content Script と Popup 間の中継。
- SaaS Backend API (`POST /api/v1/captures`) への非同期通信の実行。
- HTTP ヘッダーへの JWT (`Bearer token`) 付与と通信エラーのハンドリング。

## 4. API 通信フロー
1. ユーザーが Popup で「抽出」をクリック。
2. Service Worker が Content Script にメッセージを送信し、DOM 抽出を指示。
3. Content Script が JSON を Service Worker に返す。
4. Service Worker が `fetch` で SaaS Backend の Captures API にデータを送信。
5. Backend で eBay 照合等の処理が完了するのを待機（またはポーリング）。
6. 結果を受け取り、Content Script にメッセージを送信して画面に利益率バッジを描画。
