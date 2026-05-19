#!/usr/bin/env node
import fs from "fs";
import os from "os";
import path from "path";

function expandHome(p) {
  return p.startsWith("~") ? path.join(os.homedir(), p.slice(1)) : p;
}

async function main() {
  const args = process.argv.slice(2);
  const idx = args.indexOf("--config");
  if (idx === -1 || !args[idx + 1]) {
    console.log(JSON.stringify({ status: "error_prepare_digest", message: "Missing --config" }));
    process.exit(12);
  }

  const configPath = expandHome(args[idx + 1]);
  if (!fs.existsSync(configPath)) {
    console.log(JSON.stringify({ status: "error_prepare_digest", message: "Config not found" }));
    process.exit(12);
  }

  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const statePath = expandHome(config.state_path);
  const stateDir = path.dirname(statePath);
  fs.mkdirSync(stateDir, { recursive: true });
  const state = readState(statePath);

  let feed;
  try {
    const res = await fetch(config.feed_url);
    if (!res.ok) {
      console.log(JSON.stringify({ status: "error_fetch_feed", message: `HTTP ${res.status}` }));
      process.exit(10);
    }
    feed = await res.json();
  } catch (err) {
    console.log(JSON.stringify({ status: "error_fetch_feed", message: String(err) }));
    process.exit(10);
  }

  const topics = new Set(config.filters?.topics || []);
  const maxItems = config.filters?.max_items || 5;
  const lang = config.filters?.language || "zh";
  const items = (feed.items || [])
    .filter(item => topics.size === 0 || topics.has(item.topic))
    .filter(item => !Array.isArray(item.language) || item.language.includes(lang))
    .filter(item => !state.delivered_item_ids.includes(item.id))
    .slice(0, maxItems);

  if (items.length === 0) {
    console.log(JSON.stringify({
      run_at: new Date().toISOString(),
      feed_version: feed.generated_at || null,
      status: "skipped_no_new_items",
      selected_items: [],
      message_markdown: ""
    }, null, 2));
    process.exit(0);
  }

  const message = items.map((item, i) => {
    const summary = lang === "en" ? item.summary.en : item.summary.zh;
    return `${i + 1}. ${item.title}\n${summary}\n${item.links.abs}`;
  }).join("\n\n");

  console.log(JSON.stringify({
    run_at: new Date().toISOString(),
    feed_version: feed.generated_at || null,
    status: "ok",
    selected_items: items,
    message_markdown: message
  }, null, 2));
}

main().catch(err => {
  console.log(JSON.stringify({ status: "error_prepare_digest", message: String(err) }));
  process.exit(12);
});

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
