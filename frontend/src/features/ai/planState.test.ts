import { describe, expect, it } from "vitest"
import type { PlanItem, PlanRun } from "@/types"
import { groupByDay, isActive, stepLabel } from "./planState"

const item = (day: string, title: string): PlanItem => ({ card_id: title, title, day, reason: "" })
const run = (status: PlanRun["status"]): PlanRun => ({ id: "r", status, steps: [], result: null, error_message: "" })

describe("groupByDay", () => {
  it("orders days Monday to Sunday and skips empty days", () => {
    const groups = groupByDay([item("Friday", "c"), item("Monday", "a"), item("Friday", "d"), item("Sunday", "e")])
    expect(groups.map((g) => g.day)).toEqual(["Monday", "Friday", "Sunday"])
    expect(groups[1].items.map((i) => i.title)).toEqual(["c", "d"])
  })

  it("drops items with an unknown day instead of crashing", () => {
    expect(groupByDay([item("Someday", "x")])).toEqual([])
  })
})

describe("isActive", () => {
  it("is true only while queued or running", () => {
    expect(isActive(run("queued"))).toBe(true)
    expect(isActive(run("running"))).toBe(true)
    expect(isActive(run("succeeded"))).toBe(false)
    expect(isActive(run("failed"))).toBe(false)
    expect(isActive(undefined)).toBe(false)
  })
})

describe("stepLabel", () => {
  it("falls back to the raw step name", () => {
    expect(stepLabel("gather")).toBe("Reading open cards")
    expect(stepLabel("mystery")).toBe("mystery")
  })
})
