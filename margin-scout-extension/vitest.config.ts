import { defineConfig } from "vitest/config"
import path from "path"

export default defineConfig({
  test: {
    environment: "jsdom",
    alias: {
      "~services": path.resolve(__dirname, "./src/services"),
      "~contents": path.resolve(__dirname, "./src/contents"),
      "~background": path.resolve(__dirname, "./src/background")
    }
  }
})
