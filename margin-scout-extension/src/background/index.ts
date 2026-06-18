import axios from "axios"

const API_TIMEOUT_MS = 30000

interface CaptureMessage {
  action: "capture"
  source: string
  items: Array<{
    title: string
    price_jpy: number
    url: string
    seller_name?: string
    condition?: string
    fetched_at: string
    image_url?: string
  }>
}

interface CaptureResponse {
  success: boolean
  import_session_id?: string
  error?: string
  matched_count?: number
}

chrome.runtime.onMessage.addListener(async (message: CaptureMessage, sender, sendResponse) => {
  if (message.action === "capture") {
    try {
      // Token と endpoint を取得
      const { apiEndpoint, token } = await chrome.storage.local.get([
        "apiEndpoint",
        "token",
      ])

      if (!token) {
        sendResponse({
          success: false,
          error: "Token not configured. Go to Extension options.",
        } as CaptureResponse)
        return
      }

      // SaaS API に POST
      const response = await axios.post(
        `${apiEndpoint}/captures`,
        {
          source: message.source,
          import_type: "manual",
          items: message.items,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          timeout: API_TIMEOUT_MS,
        }
      )

      sendResponse({
        success: true,
        import_session_id: response.data.import_session_id,
        matched_count: response.data.matched_count,
      } as CaptureResponse)
    } catch (error: any) {
      console.error("Capture error:", error)
      sendResponse({
        success: false,
        error: error.message || "Unknown error",
      } as CaptureResponse)
    }
  }
})

export {}
