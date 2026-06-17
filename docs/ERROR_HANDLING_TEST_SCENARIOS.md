# エラーハンドリング検証シナリオ (Day 3-5)

## 概要
MarginScout v2.1 の異常系検証を 3 段階で実施。各段階で特定のエラータイプをシミュレートし、UI・ログ・エラーメッセージの挙動を検証。

---

## Day 3: ネットワークエラー検証 (パターン 1)

### シナリオ
1. **準備フェーズ**
   - Backend を完全に停止
   - Frontend: `http://localhost:5173` を開く
   - S01 (リサーチ開始) 画面を表示

2. **実行フェーズ**
   - キーワード: "iPhone"
   - ソース: 全選択
   - "リサーチ開始" ボタンをクリック

3. **検証フェーズ**
   - ErrorModal 表示確認: "Connection refused" メッセージが表示されるか
   - LogPanel に `error` ログが記録されるか
   - "再試行" ボタンが表示されるか
   - Backend 再起動後、再試行ボタンで正常に続行できるか

### 期待値
```
✅ ErrorModal: Connection refused (または Network Error)
✅ LogPanel: [ERROR] POST /api/research/jobs failed: ...
✅ 再試行ボタン: 存在・クリック可能
✅ Backend 再起動後: 再試行で S02 へ正常遷移
```

### チェックリスト
- [ ] ErrorModal タイトル正確性
- [ ] エラーメッセージ内容正確性
- [ ] ログレベル (ERROR) 正確性
- [ ] 再試行ボタン動作
- [ ] UI 崩れなし

---

## Day 4: API タイムアウト検証 (パターン 2)

### シナリオ
1. **準備フェーズ**
   - `margin-scout-backend/app/main.py` の POST `/api/research/jobs` に一時的に以下を追加:
     ```python
     await asyncio.sleep(35)  # timeout: 30s で強制タイムアウト
     ```
   - Backend 再起動（注入コード適用）
   - Frontend リロード

2. **実行フェーズ**
   - S01 でリサーチ開始

3. **検証フェーズ**
   - 30 秒後、ErrorModal に "Request Timeout" 表示
   - ステータス: error に更新
   - LogPanel に warning ログ記録
   - 再試行可否

### 期待値
```
✅ ErrorModal: Request Timeout
✅ LogPanel: [WARNING] Request timed out after 30s
✅ ステータス表示: error (赤)
✅ 再試行: 可能 (ただし再度タイムアウト)
```

### チェックリスト
- [ ] timeout エラーメッセージ
- [ ] ステータス表示更新 (error)
- [ ] ログレベル (WARNING)
- [ ] UI 反応継続 (フリーズなし)
- [ ] **重要**: 検証後、sleep(35) コードを削除して main に戻す

---

## Day 5: 不正 job_id 検証 (パターン 3)

### シナリオ
1. **準備フェーズ**
   - Backend 正常起動
   - Frontend: S01 → S05 フロー完全実行
   - S03 (候補一覧) まで到達

2. **検証フェーズ**
   - ブラウザコンソール (F12) を開く
   - localStorage を確認: `console.log(localStorage.getItem('job_id'))`
   - **job_id を不正値に変更**: `localStorage.setItem('job_id', 'invalid_12345')`
   - S04 (詳細) ページへナビゲート試行

3. **確認フェーズ**
   - ErrorModal: "Job not found (404)" 表示
   - LogPanel: error ログ記録
   - S03 へ戻せるか確認

### 期待値
```
✅ ErrorModal: Job not found
✅ HTTP Status: 404
✅ LogPanel: [ERROR] GET /api/research/jobs/invalid_12345 returned 404
✅ 戻るボタン: S03 に正常遷移
```

### チェックリスト
- [ ] 404 エラー検出
- [ ] エラーメッセージ正確性
- [ ] ログ記録
- [ ] 画面遷移正常性
- [ ] **重要**: localStorage を元の job_id に戻す

---

## 全段階共通の検証項目

| 項目 | Day 3 | Day 4 | Day 5 |
|---|---|---|---|
| ErrorModal 表示 | ✅ | ✅ | ✅ |
| LogPanel 記録 | ✅ | ✅ | ✅ |
| エラーメッセージ正確 | ✅ | ✅ | ✅ |
| UI フリーズなし | ✅ | ✅ | ✅ |
| 再試行または復帰 | ✅ | ✅ | ✅ |
| コンソールエラーなし | ✅ | ✅ | ✅ |

---

## 実行順序と期間
- **Day 3** (約 15 分): ネットワークエラー
- **Day 4** (約 20 分): タイムアウト
- **Day 5** (約 10 分): 不正 job_id
- **結果記録**: 各日終了後に `day_X_report.md` に記入

---

## 重要: コード修正の注意
- **Day 4 のタイムアウト注入**: 検証終了後、**必ず `sleep(35)` コードを削除** してから main ブランチにコミット
- **localStorage 変更**: Day 5 検証終了後、**必ず元の job_id に戻す** またはブラウザキャッシュをクリア

---

## GO/NO-GO 判定
- **GO**: 全パターン 3/3 成功、全チェックリスト ✅、UI 安定性確認
- **NO-GO**: 1 つ以上の失敗、再現不可能なエラー、ドキュメント不一致
