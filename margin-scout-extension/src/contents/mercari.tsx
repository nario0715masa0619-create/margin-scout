import React, { useState } from "react"
import { createRoot } from "react-dom/client"
import { MercariParser } from "~services/dom-parser"
import cssText from "data-text:~style.css"

export const getStyle = () => {
  const style = document.createElement("style")
  style.textContent = cssText
  return style
}

function MercariCaptureButton() {
  const [isCapturing, setIsCapturing] = useState(false)
  const [result, setResult] = useState<{ status: "idle" | "success" | "error"; message?: string }>({
    status: "idle",
  })

  const handleCapture = async () => {
    setIsCapturing(true)
    try {
      const items = MercariParser.extractItems()

      if (items.length === 0) {
        setResult({ status: "error", message: "商品が見つかりませんでした" })
        setIsCapturing(false)
        return
      }

      // Service Worker にメッセージ送信
      chrome.runtime.sendMessage(
        {
          action: "capture",
          source: "mercari",
          items,
        },
        (response) => {
          if (response?.success) {
            setResult({
              status: "success",
              message: `${response.matched_count}件の商品をマッチングしました`,
            })
          } else {
            setResult({
              status: "error",
              message: response?.error || "エラーが発生しました",
            })
          }
          setIsCapturing(false)
          setTimeout(() => setResult({ status: "idle" }), 3000)
        }
      )
    } catch (error: any) {
      setResult({ status: "error", message: error.message })
      setIsCapturing(false)
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={handleCapture}
        disabled={isCapturing}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg shadow-lg hover:bg-blue-600 disabled:opacity-50"
      >
        {isCapturing ? "取得中..." : "この画面から取得"}
      </button>
      {result.status === "success" && (
        <div className="mt-2 p-2 bg-green-100 text-green-800 rounded text-sm">{result.message}</div>
      )}
      {result.status === "error" && (
        <div className="mt-2 p-2 bg-red-100 text-red-800 rounded text-sm">{result.message}</div>
      )}
    </div>
  )
}

// ページ読み込み時に検出
if (MercariParser.isListPage()) {
  const container = document.createElement("div")
  document.body.appendChild(container)
  createRoot(container).render(<MercariCaptureButton />)
}
