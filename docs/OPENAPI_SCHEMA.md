# FastAPI app.py に追加する OpenAPI 設定コード
# app = FastAPI(...) 直後に以下を追加

tags_metadata = [
    {
        "name": "Research Jobs",
        "description": "リサーチジョブの管理エンドポイント",
    },
    {
        "name": "Results",
        "description": "リサーチ結果の取得エンドポイント",
    },
    {
        "name": "Export",
        "description": "CSV エクスポート関連エンドポイント",
    },
]

# app の初期化時に openapi_tags を指定
app = FastAPI(
    title="MarginScout Research API",
    description="日本国内ソース × eBay 価格照合リサーチツール API",
    version="2.1.0",
    openapi_tags=tags_metadata,
)
