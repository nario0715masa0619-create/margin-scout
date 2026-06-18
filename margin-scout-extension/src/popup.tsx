import React, { useEffect, useState } from "react"
import "~style.css"

interface CaptureHistory {
  session_id: string
  source: string
  item_count: number
  matched_count: number
  timestamp: string
}

export default function Popup() {
  const [history, setHistory] = useState<CaptureHistory[]>([])
  const [isConfigured, setIsConfigured] = useState(false)

  useEffect(() => {
    chrome.storage.local.get(["token"], (result) => {
      setIsConfigured(!!result.token)
    })
  }, [])

  return (
    <div className="w-80 p-4 bg-white">
      <h1 className="text-lg font-bold mb-4">MarginScout</h1>

      {!isConfigured ? (
        <div className="bg-yellow-100 p-3 rounded mb-4">
          <p className="text-sm mb-2">⚠️ Extension がまだ設定されていません</p>
          <button
            onClick={() => chrome.runtime.openOptionsPage()}
            className="w-full px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
          >
            設定を開く
          </button>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-600 mb-4">✅ 設定完了</p>
          <button
            onClick={() => chrome.runtime.openOptionsPage()}
            className="w-full px-3 py-1 mb-2 bg-gray-200 text-gray-800 text-sm rounded hover:bg-gray-300"
          >
            設定変更
          </button>
        </div>
      )}

      <p className="text-xs text-gray-500 mt-4">
        フリマアプリの商品一覧ページから「この画面から取得」ボタンをクリックして、商品を取得します。
      </p>
    </div>
  )
}
