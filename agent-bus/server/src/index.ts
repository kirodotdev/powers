#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod/v3";
import * as fs from "node:fs";
import * as path from "node:path";

const BUS_DIR = process.env.KIRO_AGENT_BUS_DIR ?? "/tmp/kiro-agent-bus";
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

const server = new McpServer({
  name: "agent-bus",
  version: "0.1.0",
});

// --- agent_post_message ---
server.tool(
  "agent_post_message",
  "Post a message to another agent's inbox",
  {
    from: z.string().describe("Sender agent ID"),
    to: z.string().describe("Recipient agent ID"),
    body: z.string().describe("Message content"),
  },
  async ({ from, to, body }) => {
    ensureDirs();
    registerAgent(from);
    const inbox = path.join(MESSAGES_DIR, to);
    fs.mkdirSync(inbox, { recursive: true });
    const msg = { from, to, body, timestamp: Date.now() };
    const file = path.join(inbox, `${msg.timestamp}-${from}.json`);
    fs.writeFileSync(file, JSON.stringify(msg));
    return { content: [{ type: "text", text: JSON.stringify({ ok: true, delivered: file }) }] };
  }
);

// --- agent_read_messages ---
server.tool(
  "agent_read_messages",
  "Read messages from an agent's inbox",
  {
    agent_id: z.string().describe("Agent whose inbox to read"),
    from: z.string().optional().describe("Filter by sender"),
    clear: z.boolean().optional().describe("Clear messages after reading"),
  },
  async ({ agent_id, from, clear }) => {
    ensureDirs();
    const inbox = path.join(MESSAGES_DIR, agent_id);
    if (!fs.existsSync(inbox)) {
      return { content: [{ type: "text", text: JSON.stringify({ messages: [] }) }] };
    }
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
  }
);

// --- agent_signal ---
server.tool(
  "agent_signal",
  "Set a named signal that other agents can wait on",
  {
    name: z.string().describe("Signal name"),
    payload: z.string().optional().describe("Optional data attached to the signal"),
  },
  async ({ name, payload }) => {
    ensureDirs();
    const file = path.join(SIGNALS_DIR, `${name}.json`);
    const data = { name, payload: payload ?? null, timestamp: Date.now() };
    fs.writeFileSync(file, JSON.stringify(data));
    return { content: [{ type: "text", text: JSON.stringify({ ok: true, signal: name }) }] };
  }
);

// --- agent_wait_signal ---
server.tool(
  "agent_wait_signal",
  "Check if a named signal has been set. Returns immediately with status.",
  {
    name: z.string().describe("Signal name to check"),
    timeout_ms: z.number().optional().describe("Max wait time in ms (default: 0, non-blocking)"),
  },
  async ({ name, timeout_ms }) => {
    ensureDirs();
    const file = path.join(SIGNALS_DIR, `${name}.json`);
    const deadline = Date.now() + (timeout_ms ?? 0);

    while (true) {
      if (fs.existsSync(file)) {
        const data = JSON.parse(fs.readFileSync(file, "utf-8"));
        return { content: [{ type: "text", text: JSON.stringify({ found: true, signal: data }) }] };
      }
      if (Date.now() >= deadline) {
        return { content: [{ type: "text", text: JSON.stringify({ found: false, signal: name }) }] };
      }
      await new Promise((r) => setTimeout(r, Math.min(100, deadline - Date.now())));
    }
  }
);

// --- agent_list_agents ---
server.tool(
  "agent_list_agents",
  "List all agents registered on the bus",
  {},
  async () => {
    ensureDirs();
    const files = fs.readdirSync(AGENTS_DIR);
    const agents = files.map((f) => JSON.parse(fs.readFileSync(path.join(AGENTS_DIR, f), "utf-8")));
    return { content: [{ type: "text", text: JSON.stringify({ agents }) }] };
  }
);

async function main(): Promise<void> {
  ensureDirs();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
