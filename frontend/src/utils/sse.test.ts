import { describe, expect, it } from "vitest"
import { createSSEParser, type SSEMessage } from "./sse"

function collect() {
  const messages: SSEMessage[] = []
  return { messages, feed: createSSEParser((message) => messages.push(message)) }
}

describe("createSSEParser", () => {
  it("parses a complete event", () => {
    const { messages, feed } = collect()
    feed('event: text\ndata: {"text":"hi"}\n\n')
    expect(messages).toEqual([{ event: "text", data: '{"text":"hi"}' }])
  })

  it("waits for the blank line before emitting", () => {
    const { messages, feed } = collect()
    feed("event: text\ndata: one")
    expect(messages).toEqual([])
    feed("\n\n")
    expect(messages).toHaveLength(1)
  })

  it("reassembles an event split across chunks", () => {
    const { messages, feed } = collect()
    feed("event: te")
    feed('xt\ndata: {"a"')
    feed(":1}\n\nevent: done\ndata: {}\n\n")
    expect(messages.map((m) => m.event)).toEqual(["text", "done"])
    expect(messages[0].data).toBe('{"a":1}')
  })

  it("handles several events in one chunk", () => {
    const { messages, feed } = collect()
    feed("event: a\ndata: 1\n\nevent: b\ndata: 2\n\nevent: c\ndata: 3\n\n")
    expect(messages.map((m) => m.data)).toEqual(["1", "2", "3"])
  })

  it("accepts CRLF line endings", () => {
    const { messages, feed } = collect()
    feed("event: a\r\ndata: 1\r\n\r\n")
    expect(messages).toEqual([{ event: "a", data: "1" }])
  })

  it("defaults the event name and ignores events without data", () => {
    const { messages, feed } = collect()
    feed("data: plain\n\nevent: empty\n\n")
    expect(messages).toEqual([{ event: "message", data: "plain" }])
  })
})
