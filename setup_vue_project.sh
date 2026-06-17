#!/bin/bash
# margin-scout-ui プロジェクト初期化

cd $PROJECT_ROOT

# Vue 3 + Vite プロジェクト作成
npm create vite@latest margin-scout-ui -- --template vue-ts

cd margin-scout-ui

# 依存パッケージインストール
npm install

# Pinia インストール
npm install pinia

# Vue Router インストール
npm install vue-router

# Axios インストール
npm install axios

# 開発サーバー起動確認
echo "✅ Vue 3 プロジェクト初期化完了"
echo "起動: npm run dev"
