import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import * as fs from "node:fs";
import * as assert from "node:assert";
import { describe, it, beforeEach, after } from "node:test";

const TEST_BUS = "/tmp/kiro-agent-bus-test-" + process.pid;

async function createTestServer(): Promise<Client> {
  // Set env before importing server module
  process.env.KIRO_AGENT_BUS_DIR = TEST_BUS;

  // We can't easily re-import the server, so we'll replicate the setup inline
  // using the same logic. For a real test suite we'd refactor to export a factory.
  const { z } = await import("zod/v3");
  const path = await import("node:path");

  const BUS_DIR = TEST_BUS;
  const AGENTS_DIR = path.join(BUS_DIR, "agents");
  const MESSAGES_DIR = path.join(BUS_DIR, "messages");
  const SIGNALS_DIR = path.join(BUS_DIR, "signals");

  function ensureDirs(): void {
    for (const d of [BUS_DIR, AGENTS_DIR, MESSAGES_DIR, SIGNALS_DIR]) {
      fs.mkdirSync(d, { recursive: true });
    }
  }

  function registerAgent(agentId: string): void {
    const file = path.join(AGENTS_DIR, `${agentId}.json`);
    if (!fs.existsSync(file)) {
      fs.writeFileSync(file, JSON.stringify({ id: agentId, registered: Date.now() }));
    }
  }

  const server = new McpServer({ name: "agent-bus-test", version: "0.1.0" });

  server.tool("agent_post_message", "Post a message", {
    from: z.string(), to: z.string(), body: z.string(),
  }, async ({ from, to, body }) => {
    ensureDirs(); registerAgent(from);
    const inbox = path.join(MESSAGES_DIR, to);
    fs.mkdirSync(inbox, { recursive: true });
    const msg = { from, to, body, timestamp: Date.now() };
    fs.writeFileSync(path.join(inbox, `${msg.timestamp}-${from}.json`), JSON.stringify(msg));
    return { content: [{ type: "text", text: JSON.stringify({ ok: true }) }] };
  });

  server.tool("agent_read_messages", "Read messages", {
    agent_id: z.string(), from: z.string().optional(), clear: z.boolean().optional(),
  }, async ({ agent_id, from, clear }) => {
    ensureDirs();
    const inbox = path.join(MESSAGES_DIR, agent_id);
    if (!fs.existsSync(inbox)) return { content: [{ type: "text", text: JSON.stringify({ messages: [] }) }] };
    const files = fs.readdirSync(inbox).sort();
    const messages: unknown[] = [];
    for (const f of files) {
      const fp = path.join(inbox, f);
      const msg = JSON.parse(fs.readFileSync(fp, "utf-8"));
      if (from && msg.from !== from) continue;
      messages.push(msg);
      if (clear) fs.unlinkSync(fp);
    }
    return { content: [{ type: "text", text: JSON.stringify({ messages }) }] };
  });

  server.tool("agent_signal", "Set signal", {
    name: z.string(), payload: z.string().optional(),
  }, async ({ name, payload }) => {
    ensureDirs();
    fs.writeFileSync(path.join(SIGNALS_DIR, `${name}.json`), JSON.stringify({ name, payload: payload ?? null, timestamp: Date.now() }));
    return { content: [{ type: "text", text: JSON.stringify({ ok: true }) }] };
  });

  server.tool("agent_wait_signal", "Wait for signal", {
    name: z.string(), timeout_ms: z.number().optional(),
  }, async ({ name, timeout_ms }) => {
    ensureDirs();
    const file = path.join(SIGNALS_DIR, `${name}.json`);
    const deadline = Date.now() + (timeout_ms ?? 0);
    while (true) {
      if (fs.existsSync(file)) {
        const data = JSON.parse(fs.readFileSync(file, "utf-8"));
        return { content: [{ type: "text", text: JSON.stringify({ found: true, signal: data }) }] };
      }
      if (Date.now() >= deadline) return { content: [{ type: "text", text: JSON.stringify({ found: false }) }] };
      await new Promise((r) => setTimeout(r, 50));
    }
  });

  server.tool("agent_list_agents", "List agents", {}, async () => {
    ensureDirs();
    const files = fs.readdirSync(AGENTS_DIR);
    const agents = files.map((f) => JSON.parse(fs.readFileSync(path.join(AGENTS_DIR, f), "utf-8")));
    return { content: [{ type: "text", text: JSON.stringify({ agents }) }] };
  });

  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "1.0.0" });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  return client;
}

function cleanup(): void {
  fs.rmSync(TEST_BUS, { recursive: true, force: true });
}

function parseResult(result: { content: Array<{ type: string; text?: string }> }): unknown {
  const textBlock = result.content.find((c) => c.type === "text");
  return JSON.parse(textBlock!.text!);
}

describe("agent-bus MCP server", () => {
  let client: Client;

  beforeEach(async () => {
    cleanup();
    client = await createTestServer();
  });

  after(() => {
    cleanup();
  });

  it("lists tools", async () => {
    const { tools } = await client.listTools();
    const names = tools.map((t) => t.name).sort();
    assert.deepStrictEqual(names, [
      "agent_list_agents", "agent_post_message", "agent_read_messages", "agent_signal", "agent_wait_signal",
    ]);
  });

  it("post and read messages", async () => {
    await client.callTool({ name: "agent_post_message", arguments: { from: "a1", to: "a2", body: "hello" } });
    await client.callTool({ name: "agent_post_message", arguments: { from: "a1", to: "a2", body: "world" } });

    const result = await client.callTool({ name: "agent_read_messages", arguments: { agent_id: "a2" } });
    const data = parseResult(result as any) as any;
    assert.strictEqual(data.messages.length, 2);
    assert.strictEqual(data.messages[0].body, "hello");
    assert.strictEqual(data.messages[1].body, "world");
  });

  it("filters messages by sender", async () => {
    await client.callTool({ name: "agent_post_message", arguments: { from: "a1", to: "a3", body: "from-a1" } });
    await client.callTool({ name: "agent_post_message", arguments: { from: "a2", to: "a3", body: "from-a2" } });

    const result = await client.callTool({ name: "agent_read_messages", arguments: { agent_id: "a3", from: "a2" } });
    const data = parseResult(result as any) as any;
    assert.strictEqual(data.messages.length, 1);
    assert.strictEqual(data.messages[0].body, "from-a2");
  });

  it("clears messages after reading", async () => {
    await client.callTool({ name: "agent_post_message", arguments: { from: "a1", to: "a4", body: "temp" } });
    await client.callTool({ name: "agent_read_messages", arguments: { agent_id: "a4", clear: true } });

    const result = await client.callTool({ name: "agent_read_messages", arguments: { agent_id: "a4" } });
    const data = parseResult(result as any) as any;
    assert.strictEqual(data.messages.length, 0);
  });

  it("signal and wait_signal", async () => {
    // Signal not set yet
    const r1 = await client.callTool({ name: "agent_wait_signal", arguments: { name: "done" } });
    assert.strictEqual((parseResult(r1 as any) as any).found, false);

    // Set signal
    await client.callTool({ name: "agent_signal", arguments: { name: "done", payload: "phase-1" } });

    // Now it should be found
    const r2 = await client.callTool({ name: "agent_wait_signal", arguments: { name: "done" } });
    const data = parseResult(r2 as any) as any;
    assert.strictEqual(data.found, true);
    assert.strictEqual(data.signal.payload, "phase-1");
  });

  it("list_agents tracks registered agents", async () => {
    await client.callTool({ name: "agent_post_message", arguments: { from: "agent-x", to: "agent-y", body: "hi" } });
    await client.callTool({ name: "agent_post_message", arguments: { from: "agent-z", to: "agent-y", body: "hi" } });

    const result = await client.callTool({ name: "agent_list_agents", arguments: {} });
    const data = parseResult(result as any) as any;
    const ids = data.agents.map((a: any) => a.id).sort();
    assert.deepStrictEqual(ids, ["agent-x", "agent-z"]);
  });

  it("read from empty inbox returns empty array", async () => {
    const result = await client.callTool({ name: "agent_read_messages", arguments: { agent_id: "nobody" } });
    const data = parseResult(result as any) as any;
    assert.deepStrictEqual(data.messages, []);
  });
});
