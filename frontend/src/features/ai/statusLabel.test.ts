import { describe, expect, it } from "vitest"
import type { AiStatus } from "@/types"
import { isReady, modelLabel, statusProblem } from "./statusLabel"

const status = (change: Partial<AiStatus> = {}): AiStatus => ({
  enabled: true,
  configured: true,
  provider: "gemini",
  model: "gem-model",
  problem: null,
  ...change,
})

describe("isReady", () => {
  it("is true while loading, so there is no warning flash", () => {
    expect(isReady(undefined)).toBe(true)
  })
  it("needs both the flag and a working configuration", () => {
    expect(isReady(status())).toBe(true)
    expect(isReady(status({ enabled: false }))).toBe(false)
    expect(isReady(status({ configured: false, problem: "x" }))).toBe(false)
  })
})

describe("statusProblem", () => {
  it("is null when ready or unknown", () => {
    expect(statusProblem(status())).toBeNull()
    expect(statusProblem(undefined)).toBeNull()
  })
  it("explains a missing configuration with the server's own message", () => {
    expect(statusProblem(status({ configured: false, problem: "Set AI_MODEL to a model your 'gemini' account can use." }))).toContain("AI_MODEL")
  })
  it("explains a switched off assistant", () => {
    expect(statusProblem(status({ enabled: false }))).toContain("AI_ENABLED")
  })
  it("prefers the configuration problem when both apply", () => {
    expect(statusProblem(status({ enabled: false, configured: false, problem: "No API key." }))).toBe("No API key.")
  })
})

describe("modelLabel", () => {
  it("shows provider and model once configured", () => {
    expect(modelLabel(status())).toBe("gemini / gem-model")
    expect(modelLabel(status({ configured: false }))).toBeNull()
    expect(modelLabel(undefined)).toBeNull()
  })
})
