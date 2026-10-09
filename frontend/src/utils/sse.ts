export interface SSEMessage {
  event: string
  data: string
}

/** Incremental Server-Sent Events parser: feed it decoded text chunks as they arrive. */
export function createSSEParser(onMessage: (message: SSEMessage) => void) {
  let buffer = ""

  return function feed(chunk: string) {
    buffer += chunk.replace(/\r\n/g, "\n")
    let boundary = buffer.indexOf("\n\n")
    while (boundary !== -1) {
      const raw = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf("\n\n")

      let event = "message"
      const data: string[] = []
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim()
        else if (line.startsWith("data:")) data.push(line.slice(5).trimStart())
      }
      if (data.length) onMessage({ event, data: data.join("\n") })
    }
  }
}
