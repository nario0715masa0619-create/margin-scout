import React, { useState, useEffect } from "react"
import "~style.css"

export default function OptionsPage() {
  const [apiEndpoint, setApiEndpoint] = useState("")
  const [token, setToken] = useState("")
  const [status, setStatus] = useState<"idle" | "testing" | "success" | "error">("idle")

  useEffect(() => {
    // 保存された設定を復元
    chrome.storage.local.get(["apiEndpoint", "token"], (result) => {
      setApiEndpoint(result.apiEndpoint || "https://api.margin-scout.com/api/v1")
      setToken(result.token || "")
    })
  }, [])

  const handleSave = async () => {
    await chrome.storage.local.set({ apiEndpoint, token })
    setStatus("success")
    setTimeout(() => setStatus("idle"), 2000)
  }

  const handleTest = async () => {
    setStatus("testing")
    try {
      const response = await fetch(`${apiEndpoint}/captures/test`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        setStatus("success")
      } else {
        setStatus("error")
      }
    } catch (e) {
      setStatus("error")
    }
    setTimeout(() => setStatus("idle"), 2000)
  }

  return (
    <div className="p-6 max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-4">MarginScout Extension 設定</h1>
      
      <div className="mb-4">
        <label className="block text-sm font-semibold mb-2">API Endpoint</label>
        <input
          type="text"
          value={apiEndpoint}
          onChange={(e) => setApiEndpoint(e.target.value)}
          className="w-full px-3 py-2 border rounded"
          placeholder="https://api.margin-scout.com/api/v1"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-semibold mb-2">Bearer Token</label>
        <textarea
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="w-full px-3 py-2 border rounded font-mono text-sm"
          placeholder="eyJ0eXAiOiJKV1QiLCJhbGc..."
          rows={4}
        />
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={handleSave}
          className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          保存
        </button>
        <button
          onClick={handleTest}
          className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          接続テスト
        </button>
      </div>

      {status === "success" && <p className="text-green-600">✅ 成功</p>}
      {status === "error" && <p className="text-red-600">❌ エラー</p>}
      {status === "testing" && <p className="text-blue-600">🔄 テスト中...</p>}
    </div>
  )
}
