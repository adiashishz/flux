import { describe, expect, it } from "vitest"
import type { ChatEvent } from "@/types"
import { applyEvent, newMessage, setConfirmationState, toTurns } from "./chatState"

const assistant = () => newMessage("assistant")

describe("applyEvent", () => {
  it("appends streamed text", () => {
    const message = [{ type: "text", text: "Hel" }, { type: "text", text: "lo" }].reduce(
      (current, event) => applyEvent(current, event as ChatEvent),
      assistant()
    )
    expect(message.content).toBe("Hello")
  })

  it("tracks a tool call from running to ok", () => {
    let message = applyEvent(assistant(), { type: "tool_call", id: "t1", name: "create_card", input: { title: "A" } })
    expect(message.tools[0].status).toBe("running")
    message = applyEvent(message, { type: "tool_result", id: "t1", name: "create_card", ok: true, result: { title: "A" } })
    expect(message.tools[0]).toMatchObject({ status: "ok", result: { title: "A" } })
  })

  it("marks a failed tool as an error", () => {
    let message = applyEvent(assistant(), { type: "tool_call", id: "t1", name: "get_board", input: {} })
    message = applyEvent(message, { type: "tool_result", id: "t1", name: "get_board", ok: false, result: { error: "no" } })
    expect(message.tools[0].status).toBe("error")
  })

  it("records a delete confirmation as pending", () => {
    const message = applyEvent(assistant(), {
      type: "confirmation_required", action: "delete_card", card_id: "c1", title: "Old", board_id: "b1",
    })
    expect(message.confirmations).toEqual([{ cardId: "c1", title: "Old", boardId: "b1", state: "pending" }])
  })

  it("stores an error and ignores done", () => {
    expect(applyEvent(assistant(), { type: "error", message: "boom" }).error).toBe("boom")
    const done: ChatEvent = { type: "done", stop_reason: "end_turn", iterations: 1, usage: { input_tokens: 1, output_tokens: 1 } }
    const before = assistant()
    expect(applyEvent(before, done)).toBe(before)
  })
})

describe("setConfirmationState", () => {
  it("updates only the matching confirmation", () => {
    let message = applyEvent(assistant(), { type: "confirmation_required", action: "delete_card", card_id: "a", title: "A", board_id: "b" })
    message = applyEvent(message, { type: "confirmation_required", action: "delete_card", card_id: "c", title: "C", board_id: "b" })
    message = setConfirmationState(message, "a", "deleted")
    expect(message.confirmations.map((c) => c.state)).toEqual(["deleted", "pending"])
  })
})

describe("toTurns", () => {
  const user = (content: string) => newMessage("user", content)
  const reply = (content: string) => newMessage("assistant", content)

  it("sends only messages that have text", () => {
    expect(toTurns([user("hi"), reply(""), reply("hello")])).toEqual([
      { role: "user", content: "hi" },
      { role: "assistant", content: "hello" },
    ])
  })

  it("keeps the newest 20 turns and starts on a user turn", () => {
    const messages = Array.from({ length: 30 }, (_, i) => (i % 2 === 0 ? user(`u${i}`) : reply(`a${i}`)))
    const turns = toTurns(messages)
    expect(turns.length).toBeLessThanOrEqual(20)
    expect(turns[0].role).toBe("user")
    expect(turns[turns.length - 1].content).toBe("a29")
  })
})
