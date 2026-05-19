#!/usr/bin/env node
import fs from "fs";
import os from "os";
import path from "path";

function expandHome(p) {
  return p.startsWith("~") ? path.join(os.homedir(), p.slice(1)) : p;
}

async function main() {
  const args = process.argv.slice(2);
  const configIdx = args.indexOf("--config");
  const inputIdx = args.indexOf("--input");
  if (configIdx === -1 || inputIdx === -1 || !args[configIdx + 1] || !args[inputIdx + 1]) {
    console.log(JSON.stringify({ status: "error_delivery", message: "Missing --config or --input" }));
    process.exit(20);
  }
  const configPath = expandHome(args[configIdx + 1]);
  const inputPath = expandHome(args[inputIdx + 1]);
  if (!fs.existsSync(configPath) || !fs.existsSync(inputPath)) {
    console.log(JSON.stringify({ status: "error_delivery", message: "Config or input missing" }));
    process.exit(20);
  }
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const payload = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
  const statePath = expandHome(config.state_path);
  const stateDir = path.dirname(statePath);
  fs.mkdirSync(stateDir, { recursive: true });
  const state = readState(statePath);
  if (payload.status === "skipped_no_new_items") {
    console.log(JSON.stringify({ status: "skipped_no_new_items", message: "No delivery needed" }));
    process.exit(0);
  }
  const message = payload.message_markdown || "";
  const channel = config.delivery?.channel || "stdout";
  if (channel === "stdout") {
    await new Promise((resolve, reject) => {
      process.stdout.write(message + "\n", (err) => err ? reject(err) : resolve());
    });
    persist_state(statePath, state, payload);
    process.exit(0);
  }
  console.log(JSON.stringify({ status: "error_delivery", message: `Unsupported channel: ${channel}` }));
  process.exit(22);
}

function persist_state(statePath, state, payload) {
  const ids = new Set(state.delivered_item_ids || []);
  for (const item of payload.selected_items || []) {
    ids.add(item.id);
  }
  const nextState = {
    ...state,
    delivered_item_ids: Array.from(ids),
    last_delivered_at: new Date().toISOString(),
    last_feed_etag: payload.feed_version || null
  };
  fs.writeFileSync(statePath, JSON.stringify(nextState, null, 2) + "\n");
}

function readState(statePath) {
  if (!fs.existsSync(statePath)) {
    return { delivered_item_ids: [] };
  }
  const raw = fs.readFileSync(statePath, "utf-8").trim();
  if (!raw) {
    return { delivered_item_ids: [] };
  }
  return JSON.parse(raw);
}

main().catch(err => {
  console.log(JSON.stringify({ status: "error_delivery", message: String(err) }));
  process.exit(22);
});
