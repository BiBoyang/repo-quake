#!/usr/bin/env node
/**
 * mock.mjs — deterministic loopback mock provider for stream-retry display experiments.
 *
 * Ported from the 2026-11-14/15 xtool mocks and fixed per the 2026-11-15 verifier
 * report (witness/stream-retry/README.md lists every change).
 *
 * Protocol endpoints (one port, loopback only):
 *   POST /v1/chat/completions       OpenAI Chat Completions (SSE or JSON)
 *   POST /v1/responses              OpenAI Responses (SSE or JSON)
 *   POST /v1/messages               Anthropic Messages (SSE or JSON)
 *   GET  /v1/models, POST /v1/messages/count_tokens
 *   GET  /health                    {ok, instance} — no token needed, no state
 * Control plane (header `x-mock-token` must equal $MOCK_CONTROL_TOKEN):
 *   GET  /__control                 current state
 *   POST /__control                 {"reset":true} | {"always":"F1","profile":"long",
 *                                    "once":{"fault":"F6","match":"RUN…","avoid":["…"],"tag":"〔x…〕"}}
 *   GET  /__logs?n=20               last n delivery records
 *
 * Fault shapes: F0 healthy; F1 partial then TCP FIN; F2 full content, terminator missing,
 * clean close; F3 partial plus half an SSE event then FIN; F4 length/max_tokens; F5
 * think-only; F6 partial then a clean HTTP end with no terminator; FLONG the long partial
 * (L001–L160) at the long frame delay, then FIN.
 * Thinking shapes (phase 5): FTHINK1 a thinking block (R01–R06) and nothing else, then
 * TCP FIN; FTHINK6 the same thinking, then a clean HTTP end with no terminator; F0T healthy
 * with a complete thinking block before the full answer (positive control for thinking
 * display). A tag marks the thinking these three (and F5) stream; F0T's text stays untagged.
 *
 * Once-faults are consumed only by a streaming, non-auxiliary request whose raw body
 * contains `match` and none of `avoid`. Auxiliary = the request asks for structured JSON
 * output (title generation), or (phase 5) its raw body contains one of the control plane's
 * `aux_match` strings: a subject whose title request is plain text declares its signature. A non-streaming request never consumes a once-fault; when the
 * always-fault is not F0 it is failed too (headers, then FIN).
 *
 * Delivery proof: <logdir>/delivery.jsonl, one record per request (ms timestamps, fault and
 * its source, events, bytes, ending, continuation decision, request sha256);
 * <logdir>/req-<seq>.json keeps every request body, written once and never overwritten.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FAULTS = new Set(['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'FLONG', 'F0T', 'FTHINK1', 'FTHINK6']);
const THINKING_FAULTS = new Set(['F0T', 'F5', 'FTHINK1', 'FTHINK6']);
const PROFILES = new Set(['short', 'long', 'ack']);
const CONTINUATION_MODES = new Set(['restart', 'continue', 'documented']);
const LOOPBACK = new Set(['127.0.0.1', '::1']);

function die(message) {
  console.error(`[mock] ${message}`);
  process.exit(2);
}

function parseArgs(argv) {
  const a = {
    host: '127.0.0.1', port: 0, delay: 20, longDelay: 150, logdir: null, readyFile: null,
    content: path.join(HERE, 'content.json'), continuation: 'restart', fault: 'F0',
  };
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) die(`missing value for ${key}`);
      return argv[++i];
    };
    switch (key) {
      case '--host': a.host = next(); break;
      case '--port': a.port = Number(next()); break;
      case '--delay': a.delay = Number(next()); break;
      case '--long-delay': a.longDelay = Number(next()); break;
      case '--logdir': a.logdir = next(); break;
      case '--ready-file': a.readyFile = next(); break;
      case '--content': a.content = next(); break;
      case '--continuation': a.continuation = next(); break;
      case '--fault': a.fault = next().toUpperCase(); break;
      default: die(`unknown argument: ${key}`);
    }
  }
  if (!LOOPBACK.has(a.host)) die(`refusing non-loopback host ${a.host}`);
  if (!Number.isInteger(a.port) || a.port < 0 || a.port > 65535) die(`invalid --port ${a.port}`);
  for (const k of ['delay', 'longDelay']) {
    if (!Number.isFinite(a[k]) || a[k] < 0) die(`invalid --${k === 'delay' ? 'delay' : 'long-delay'}`);
  }
  if (!a.logdir) die('--logdir is required');
  if (!CONTINUATION_MODES.has(a.continuation)) die(`invalid --continuation ${a.continuation}`);
  if (!FAULTS.has(a.fault)) die(`invalid --fault ${a.fault}`);
  return a;
}

const ARGS = parseArgs(process.argv);
const TOKEN = process.env.MOCK_CONTROL_TOKEN || '';
if (TOKEN.length < 16) die('MOCK_CONTROL_TOKEN must be set (at least 16 characters)');
const INSTANCE = process.env.MOCK_INSTANCE || crypto.randomBytes(8).toString('hex');

const CONTENT_RAW = fs.readFileSync(ARGS.content);
const CONTENT = JSON.parse(CONTENT_RAW.toString('utf8'));
const CONTENT_SHA256 = crypto.createHash('sha256').update(CONTENT_RAW).digest('hex');
const FULL = { short: CONTENT.short, long: CONTENT.long, ack: CONTENT.ack };
const PARTIAL_LEN = { short: CONTENT.short_partial, long: CONTENT.long_partial, ack: CONTENT.ack.length };
const Q_SERIES = CONTENT.short.map((t) => t.replace(/【P(\d\d)】/g, '【Q$1】'));

fs.mkdirSync(ARGS.logdir, { recursive: true });
const LOG_PATH = path.join(ARGS.logdir, 'delivery.jsonl');
if (fs.existsSync(LOG_PATH)) die(`logdir already holds a delivery log: ${LOG_PATH} (use a fresh logdir per mock)`);

// aux_match (phase 5): body substrings that mark a subject's auxiliary requests (e.g. a title
// request that is neither structured nor distinguishable otherwise); see isAux()
const state = { always: ARGS.fault, profile: 'short', once: null, aux_match: [] };
let reqSeq = 0;
let idSeq = 0;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------------- request inspection ----------------
function textOf(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) return content.map(textOf).join('');
  if (content && typeof content === 'object') {
    if (typeof content.text === 'string') return content.text;
    if ('content' in content) return textOf(content.content);
  }
  return '';
}

function messagesOf(endpoint, body) {
  if (endpoint === 'responses') {
    const input = Array.isArray(body.input) ? body.input : [];
    return input.filter((item) => item && typeof item === 'object' && item.role);
  }
  return Array.isArray(body.messages) ? body.messages : [];
}

function assistantTexts(endpoint, body) {
  return messagesOf(endpoint, body).filter((m) => m.role === 'assistant').map((m) => textOf(m.content));
}

function isStructured(body) {
  for (const key of ['output_config', 'text', 'response_format', 'output_format']) {
    if (body[key] && JSON.stringify(body[key]).includes('"json_schema"')) return true;
  }
  return false;
}

function markerFamily(text) {
  const ls = [...text.matchAll(/【L(\d{3})】/g)].map((m) => Number(m[1]));
  const ps = [...text.matchAll(/【P(\d{2})】/g)].map((m) => Number(m[1]));
  if (ls.length) return { family: 'long', max: Math.max(...ls) };
  if (ps.length) return { family: 'short', max: Math.max(...ps) };
  return null;
}

function continuationDecision(endpoint, body) {
  const msgs = messagesOf(endpoint, body);
  const last = msgs[msgs.length - 1];
  const info = { mode: ARGS.continuation, trailing_assistant: false, partial_flag: false, trailing_family: null, trailing_max: null, decision: 'none' };
  if (!last || last.role !== 'assistant') return info;
  info.trailing_assistant = true;
  info.partial_flag = last.partial === true;
  const fam = markerFamily(textOf(last.content));
  if (!fam) return info;
  info.trailing_family = fam.family;
  info.trailing_max = fam.max;
  if (ARGS.continuation === 'restart') info.decision = 'restart';
  else if (ARGS.continuation === 'continue') info.decision = 'continue';
  else if (endpoint === 'cc') info.decision = info.partial_flag ? 'continue' : 'restart'; // Kimi/Moonshot Partial Mode
  else if (endpoint === 'anthropic') info.decision = 'continue'; // documented assistant prefill
  else info.decision = 'restart'; // Responses: no documented prefill
  return info;
}

// ---------------- payload plans ----------------
const sseEvent = (event, data) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
const sseData = (data) => `data: ${typeof data === 'string' ? data : JSON.stringify(data)}\n\n`;

function withTag(paras, tag, upto) {
  if (!tag) return paras;
  return paras.map((p, i) => (i < upto ? `${p} ${tag}` : p));
}

// Select the paragraphs a response carries. Returns {prof, full, partial, reasoning}.
function selectContent(fault, profile, tag, cont) {
  const prof = fault === 'FLONG' ? 'long' : profile;
  let full = FULL[prof];
  if (cont && cont.decision === 'continue' && cont.trailing_family) {
    full = FULL[cont.trailing_family].slice(cont.trailing_max);
  }
  const partialLen = PARTIAL_LEN[prof];
  const partial = full.slice(0, partialLen);
  if (THINKING_FAULTS.has(fault)) {
    // the tag marks the thinking this response streams; any text it carries (F0T) is untagged
    return { prof, full, partial, reasoning: withTag(CONTENT.reasoning, tag, CONTENT.reasoning.length) };
  }
  const reasoning = CONTENT.reasoning;
  if (fault === 'F0' || fault === 'F2' || fault === 'F4') {
    return { prof, full: withTag(full, tag, partialLen), partial, reasoning };
  }
  return { prof, full, partial: withTag(partial, tag, partialLen), reasoning };
}

function buildCc(model, fault, sel) {
  const id = `chatcmpl-mock-${++idSeq}`;
  const created = Math.floor(Date.now() / 1000);
  const chunk = (delta, finish = null) => sseData({ id, object: 'chat.completion.chunk', created, model, choices: [{ index: 0, delta, finish_reason: finish }] });
  const role = { k: 'ev', tag: 'cc.role', frame: chunk({ role: 'assistant', content: '' }) };
  const content = (paras, pfx = '') => paras.map((p, i) => ({ k: 'ev', tag: `${pfx}cc.content[${i}]`, frame: chunk({ content: `${p}\n` }) }));
  const finish = (reason) => ({ k: 'ev', tag: `cc.finish(${reason})`, frame: chunk({}, reason) });
  const done = { k: 'raw', tag: 'cc.[DONE]', frame: sseData('[DONE]') };
  const roleR = { k: 'ev', tag: 'cc.role', frame: chunk({ role: 'assistant', content: null, reasoning_content: '' }) };
  const reasoning = () => sel.reasoning.map((p, i) => ({ k: 'ev', tag: `cc.reasoning[${i}]`, frame: chunk({ reasoning_content: `${p}\n` }) }));
  switch (fault) {
    case 'F0': return [role, ...content(sel.full), finish('stop'), done, { k: 'close', mode: 'clean' }];
    case 'F1': case 'FLONG': return [role, ...content(sel.partial), { k: 'close', mode: 'fin' }];
    case 'F6': return [role, ...content(sel.partial), { k: 'close', mode: 'clean' }];
    case 'F2': return [role, ...content(sel.full), done, { k: 'close', mode: 'clean' }];
    case 'F3': return [role, ...content(sel.partial), { k: 'raw', tag: 'cc.partial-event', frame: `data: {"id":"${id}","object":"chat.completion.chunk","cho` }, { k: 'close', mode: 'fin' }];
    case 'F4': return [role, ...content(sel.full), ...content(Q_SERIES, 'Q.'), finish('length'), done, { k: 'close', mode: 'clean' }];
    case 'F5': return [roleR, ...reasoning(), finish('length'), done, { k: 'close', mode: 'clean' }];
    case 'FTHINK1': return [roleR, ...reasoning(), { k: 'close', mode: 'fin' }];
    case 'FTHINK6': return [roleR, ...reasoning(), { k: 'close', mode: 'clean' }];
    case 'F0T': return [roleR, ...reasoning(), ...content(sel.full), finish('stop'), done, { k: 'close', mode: 'clean' }];
    default: throw new Error(`unhandled fault ${fault}`);
  }
}

function buildResponses(model, fault, sel) {
  const n = ++idSeq;
  const respId = `resp_mock_${n}`;
  const msgId = `msg_mock_${n}`;
  const rsId = `rs_mock_${n}`;
  const createdAt = Math.floor(Date.now() / 1000);
  const ev = (type, obj) => ({ k: 'ev', tag: type, frame: sseEvent(type, { type, ...obj }) });
  const textFull = sel.full.map((p) => `${p}\n`).join('') + (fault === 'F4' ? Q_SERIES.map((p) => `${p}\n`).join('') : '');
  const messageItem = { id: msgId, type: 'message', status: 'completed', role: 'assistant', content: [{ type: 'output_text', text: textFull, annotations: [] }] };
  const usage = { input_tokens: 42, output_tokens: 1024, total_tokens: 1066 };
  const respObj = (status, extra = {}) => ({ id: respId, object: 'response', created_at: createdAt, status, model, output: status === 'completed' || status === 'incomplete' ? [messageItem] : [], usage, ...extra });
  const created = ev('response.created', { response: respObj('in_progress') });
  const itemAdded = ev('response.output_item.added', { output_index: 0, item: { id: msgId, type: 'message', status: 'in_progress', role: 'assistant', content: [] } });
  const partAdded = ev('response.content_part.added', { item_id: msgId, output_index: 0, content_index: 0, part: { type: 'output_text', text: '' } });
  const deltas = (paras, pfx = '') => paras.map((p, i) => ({ ...ev('response.output_text.delta', { item_id: msgId, output_index: 0, content_index: 0, delta: `${p}\n` }), tag: `${pfx}response.output_text.delta[${i}]` }));
  const textDone = ev('response.output_text.done', { item_id: msgId, output_index: 0, content_index: 0, text: textFull });
  const itemDone = ev('response.output_item.done', { output_index: 0, item: messageItem });
  const completed = ev('response.completed', { response: respObj('completed') });
  const incomplete = ev('response.incomplete', { response: respObj('incomplete', { incomplete_details: { reason: 'max_output_tokens' } }) });
  const head = [created, itemAdded, partAdded];
  // reasoning summary of output item 0 (F5, FTHINK1/6, F0T); structured answers carry none
  const reasoningParas = sel.reasoning || CONTENT.reasoning;
  const rsn = reasoningParas.map((p) => `${p}\n`).join('');
  const reasoningItem = { id: rsId, type: 'reasoning', summary: [{ type: 'summary_text', text: rsn }] };
  const reasoningOpen = [
    ev('response.output_item.added', { output_index: 0, item: { id: rsId, type: 'reasoning', summary: [] } }),
    ev('response.reasoning_summary_part.added', { item_id: rsId, output_index: 0, summary_index: 0, part: { type: 'summary_text', text: '' } }),
    ...reasoningParas.map((p, i) => ({ ...ev('response.reasoning_summary_text.delta', { item_id: rsId, output_index: 0, summary_index: 0, delta: `${p}\n` }), tag: `reasoning_summary_text.delta[${i}]` })),
  ];
  const reasoningClose = [
    ev('response.reasoning_summary_text.done', { item_id: rsId, output_index: 0, summary_index: 0, text: rsn }),
    ev('response.output_item.done', { output_index: 0, item: reasoningItem }),
  ];
  switch (fault) {
    case 'F0': return [...head, ...deltas(sel.full), textDone, itemDone, completed, { k: 'close', mode: 'clean' }];
    case 'F1': case 'FLONG': return [...head, ...deltas(sel.partial), { k: 'close', mode: 'fin' }];
    case 'F6': return [...head, ...deltas(sel.partial), { k: 'close', mode: 'clean' }];
    case 'F2': return [...head, ...deltas(sel.full), textDone, itemDone, { k: 'close', mode: 'clean' }];
    case 'F3': return [...head, ...deltas(sel.partial), { k: 'raw', tag: 'responses.partial-event', frame: 'data: {"type":"response.output_text.del' }, { k: 'close', mode: 'fin' }];
    case 'F4': return [...head, ...deltas(sel.full), ...deltas(Q_SERIES, 'Q.'), textDone, itemDone, incomplete, { k: 'close', mode: 'clean' }];
    case 'F5': return [created, ...reasoningOpen, ...reasoningClose, incomplete, { k: 'close', mode: 'clean' }];
    case 'FTHINK1': return [created, ...reasoningOpen, { k: 'close', mode: 'fin' }];
    case 'FTHINK6': return [created, ...reasoningOpen, { k: 'close', mode: 'clean' }];
    case 'F0T': {
      // reasoning is output item 0, the message output item 1
      const at1 = (type, obj) => ev(type, { ...obj, output_index: 1 });
      const deltas1 = sel.full.map((p, i) => ({ ...at1('response.output_text.delta', { item_id: msgId, content_index: 0, delta: `${p}\n` }), tag: `response.output_text.delta[${i}]` }));
      const done = ev('response.completed', { response: { ...respObj('completed'), output: [reasoningItem, messageItem] } });
      return [created, ...reasoningOpen, ...reasoningClose,
        at1('response.output_item.added', { item: { id: msgId, type: 'message', status: 'in_progress', role: 'assistant', content: [] } }),
        at1('response.content_part.added', { item_id: msgId, content_index: 0, part: { type: 'output_text', text: '' } }),
        ...deltas1,
        at1('response.output_text.done', { item_id: msgId, content_index: 0, text: textFull }),
        at1('response.output_item.done', { item: messageItem }),
        done, { k: 'close', mode: 'clean' }];
    }
    default: throw new Error(`unhandled fault ${fault}`);
  }
}

function buildAnthropic(model, fault, sel) {
  const msgId = `msg_mock_${++idSeq}`;
  const ev = (type, obj) => ({ k: 'ev', tag: type, frame: sseEvent(type, { type, ...obj }) });
  const messageStart = ev('message_start', { message: { id: msgId, type: 'message', role: 'assistant', model, content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 24, output_tokens: 1 } } });
  const blockStart = ev('content_block_start', { index: 0, content_block: { type: 'text', text: '' } });
  const ping = ev('ping', {});
  const deltas = (paras, pfx = '', index = 0) => paras.map((p, i) => ({ ...ev('content_block_delta', { index, delta: { type: 'text_delta', text: `${p}\n` } }), tag: `${pfx}content_block_delta[${i}]` }));
  const blockStop = ev('content_block_stop', { index: 0 });
  const msgDelta = (reason) => ev('message_delta', { delta: { stop_reason: reason, stop_sequence: null }, usage: { output_tokens: 1024 } });
  const msgStop = ev('message_stop', {});
  // thinking block 0 (F5, FTHINK1/6, F0T); only a complete block (F0T) carries a signature
  const thinkStart = ev('content_block_start', { index: 0, content_block: { type: 'thinking', thinking: '' } });
  const thinking = () => sel.reasoning.map((p, i) => ({ ...ev('content_block_delta', { index: 0, delta: { type: 'thinking_delta', thinking: `${p}\n` } }), tag: `thinking_delta[${i}]` }));
  const signature = { ...ev('content_block_delta', { index: 0, delta: { type: 'signature_delta', signature: 'bW9jay10aGlua2luZy1zaWduYXR1cmU=' } }), tag: 'signature_delta' };
  switch (fault) {
    case 'F0': return [messageStart, blockStart, ping, ...deltas(sel.full), blockStop, msgDelta('end_turn'), msgStop, { k: 'close', mode: 'clean' }];
    case 'F1': case 'FLONG': return [messageStart, blockStart, ...deltas(sel.partial), { k: 'close', mode: 'fin' }];
    case 'F6': return [messageStart, blockStart, ...deltas(sel.partial), { k: 'close', mode: 'clean' }];
    case 'F2': return [messageStart, blockStart, ping, ...deltas(sel.full), blockStop, msgDelta('end_turn'), { k: 'close', mode: 'clean' }];
    case 'F3': return [messageStart, blockStart, ...deltas(sel.partial), { k: 'raw', tag: 'anthropic.partial-event', frame: 'data: {"type":"content_block_del' }, { k: 'close', mode: 'fin' }];
    case 'F4': return [messageStart, blockStart, ping, ...deltas(sel.full), ...deltas(Q_SERIES, 'Q.'), blockStop, msgDelta('max_tokens'), msgStop, { k: 'close', mode: 'clean' }];
    case 'F5': return [messageStart, thinkStart, ...thinking(), blockStop, msgDelta('max_tokens'), msgStop, { k: 'close', mode: 'clean' }];
    case 'FTHINK1': return [messageStart, thinkStart, ...thinking(), { k: 'close', mode: 'fin' }];
    case 'FTHINK6': return [messageStart, thinkStart, ...thinking(), { k: 'close', mode: 'clean' }];
    case 'F0T': return [messageStart, thinkStart, ...thinking(), signature, blockStop,
      ev('content_block_start', { index: 1, content_block: { type: 'text', text: '' } }), ping,
      ...deltas(sel.full, '', 1), ev('content_block_stop', { index: 1 }), msgDelta('end_turn'), msgStop, { k: 'close', mode: 'clean' }];
    default: throw new Error(`unhandled fault ${fault}`);
  }
}

// Structured-output (title) answers: a schema-shaped JSON object, never marker text.
function structuredText() {
  return JSON.stringify({ title: CONTENT.aux_title });
}

function buildStructuredStream(endpoint, model) {
  const text = structuredText();
  const sel = { full: [text], partial: [text], reasoning: [] };
  const plan = endpoint === 'cc' ? buildCc(model, 'F0', sel) : endpoint === 'responses' ? buildResponses(model, 'F0', sel) : buildAnthropic(model, 'F0', sel);
  // the builders append '\n' to each paragraph; that is harmless for JSON parsers
  return plan;
}

function nonStreamBody(endpoint, model, text) {
  const ts = Math.floor(Date.now() / 1000);
  const n = ++idSeq;
  if (endpoint === 'cc') return { id: `chatcmpl-mock-${n}`, object: 'chat.completion', created: ts, model, choices: [{ index: 0, message: { role: 'assistant', content: text }, finish_reason: 'stop' }], usage: { prompt_tokens: 20, completion_tokens: 1024, total_tokens: 1044 } };
  if (endpoint === 'responses') return { id: `resp_mock_${n}`, object: 'response', created_at: ts, status: 'completed', model, output: [{ id: `msg_mock_${n}`, type: 'message', status: 'completed', role: 'assistant', content: [{ type: 'output_text', text, annotations: [] }] }], usage: { input_tokens: 42, output_tokens: 1024, total_tokens: 1066 } };
  return { id: `msg_mock_${n}`, type: 'message', role: 'assistant', model, content: [{ type: 'text', text }], stop_reason: 'end_turn', stop_sequence: null, usage: { input_tokens: 24, output_tokens: 1024 } };
}

// ---------------- delivery log ----------------
function appendLog(entry) {
  fs.appendFileSync(LOG_PATH, `${JSON.stringify(entry)}\n`);
  console.log(`[mock] #${entry.seq} ${entry.endpoint} fault=${entry.fault}(${entry.fault_source}) stream=${entry.stream} aux=${entry.aux} bytes=${entry.bytes_sent} events=${entry.events_count} ending=${entry.ending} cont=${entry.continuation ? entry.continuation.decision : '-'}`);
}

function witnessesOf(events) {
  return {
    cc_done: events.includes('cc.[DONE]'),
    cc_finish_chunk: events.some((t) => t.startsWith('cc.finish(')),
    responses_completed: events.includes('response.completed'),
    responses_incomplete: events.includes('response.incomplete'),
    anthropic_message_stop: events.includes('message_stop'),
  };
}

async function runStream(res, actions, meta, delay) {
  res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8', 'cache-control': 'no-cache', connection: 'keep-alive' });
  const events = [];
  let bytes = 0;
  let ending = 'clean';
  let aborted = false;
  let firstByte = null;
  let clientClosedFirst = false;
  res.on('close', () => { if (!res.writableFinished) aborted = true; });
  for (const a of actions) {
    if (a.k === 'close') {
      ending = a.mode;
      // Every data frame (terminal witness included) is already written; a client that
      // hangs up on the terminal event before our close is not an aborted delivery.
      if (aborted) { clientClosedFirst = true; break; }
      if (a.mode === 'clean') res.end();
      else res.socket.end(); // TCP FIN; the chunked body is left unterminated
      break;
    }
    if (aborted) { ending = 'client-abort'; break; }
    res.write(a.frame);
    if (firstByte === null) firstByte = Date.now();
    bytes += Buffer.byteLength(a.frame);
    events.push(a.tag);
    if (delay > 0) await sleep(delay);
  }
  appendLog({ ...meta, stream: true, first_byte_ms: firstByte, ended_ms: Date.now(), bytes_sent: bytes, events_count: events.length, events, witnesses: witnessesOf(events), ending, client_closed_first: clientClosedFirst });
}

// ---------------- HTTP ----------------
function readBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', () => resolve(Buffer.concat(chunks)));
  });
}

function sendJson(res, code, obj) {
  res.writeHead(code, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
}

function authorized(req) {
  const given = Buffer.from(String(req.headers['x-mock-token'] || ''));
  const want = Buffer.from(TOKEN);
  return given.length === want.length && crypto.timingSafeEqual(given, want);
}

function publicState() {
  return { ok: true, instance: INSTANCE, always: state.always, profile: state.profile, once: state.once, aux_match: state.aux_match, delay_ms: ARGS.delay, long_delay_ms: ARGS.longDelay, continuation: ARGS.continuation, content_sha256: CONTENT_SHA256, requests: reqSeq };
}

function applyControl(body) {
  if (body.reset) { state.always = 'F0'; state.profile = 'short'; state.once = null; state.aux_match = []; }
  if ('aux_match' in body) {
    const m = body.aux_match == null ? [] : body.aux_match;
    if (!Array.isArray(m) || !m.every((s) => typeof s === 'string' && s)) throw new Error('aux_match must be a list of non-empty strings');
    state.aux_match = m;
  }
  if ('always' in body) {
    const f = String(body.always || '').toUpperCase();
    if (!FAULTS.has(f)) throw new Error(`always must be one of ${[...FAULTS].join(', ')}`);
    state.always = f;
  }
  if ('profile' in body) {
    if (!PROFILES.has(body.profile)) throw new Error('profile must be short, long or ack');
    state.profile = body.profile;
  }
  if ('once' in body) {
    if (body.once === null) state.once = null;
    else {
      const o = body.once;
      const f = String(o.fault || '').toUpperCase();
      if (!FAULTS.has(f)) throw new Error(`once.fault must be one of ${[...FAULTS].join(', ')}`);
      const avoid = o.avoid == null ? [] : (Array.isArray(o.avoid) ? o.avoid : [o.avoid]);
      if (!avoid.every((s) => typeof s === 'string' && s)) throw new Error('once.avoid must be strings');
      if (o.match != null && (typeof o.match !== 'string' || !o.match)) throw new Error('once.match must be a non-empty string');
      if (o.tag != null && (typeof o.tag !== 'string' || !o.tag)) throw new Error('once.tag must be a non-empty string');
      state.once = { fault: f, match: o.match || null, avoid, tag: o.tag || null, skip_aux: o.skip_aux !== false, armed_ms: Date.now() };
    }
  }
}

const ENDPOINTS = { '/v1/chat/completions': 'cc', '/v1/responses': 'responses', '/v1/messages': 'anthropic' };

const server = http.createServer(async (req, res) => {
  const startedMs = Date.now();
  const url = new URL(req.url, 'http://localhost');
  const p = url.pathname;

  if (p === '/health') return sendJson(res, 200, { ok: true, instance: INSTANCE });
  if (p === '/__control' || p === '/__logs') {
    if (!authorized(req)) { await readBody(req); return sendJson(res, 401, { ok: false, error: 'bad or missing x-mock-token' }); }
    if (p === '/__logs') {
      const n = Number(url.searchParams.get('n') || 20);
      let lines = [];
      try { lines = fs.readFileSync(LOG_PATH, 'utf8').trim().split('\n').filter(Boolean).slice(-n).map((l) => JSON.parse(l)); } catch { lines = []; }
      return sendJson(res, 200, lines);
    }
    if (req.method === 'POST') {
      let body;
      try { body = JSON.parse((await readBody(req)).toString('utf8') || '{}'); } catch { return sendJson(res, 400, { ok: false, error: 'invalid JSON' }); }
      try { applyControl(body); } catch (err) { return sendJson(res, 400, { ok: false, error: err.message }); }
      console.log(`[mock] control -> always=${state.always} profile=${state.profile} once=${state.once ? state.once.fault : 'none'}`);
    }
    return sendJson(res, 200, publicState());
  }
  if (p === '/v1/models' && req.method === 'GET') {
    const anthropic = 'x-api-key' in req.headers || 'anthropic-version' in req.headers;
    return sendJson(res, 200, anthropic
      ? { data: [{ id: 'mock-model', type: 'model', display_name: 'Mock Model', created_at: '2026-01-01T00:00:00Z' }], has_more: false, first_id: 'mock-model', last_id: 'mock-model' }
      : { object: 'list', data: [{ id: 'mock-model', object: 'model', created: 1700000000, owned_by: 'mock' }] });
  }
  if (p === '/v1/messages/count_tokens' && req.method === 'POST') { await readBody(req); return sendJson(res, 200, { input_tokens: 100 }); }

  const endpoint = ENDPOINTS[p];
  if (!endpoint || req.method !== 'POST') { await readBody(req); return sendJson(res, 404, { error: `unknown endpoint: ${req.method} ${p}` }); }

  const raw = await readBody(req);
  const rawText = raw.toString('utf8');
  let body;
  try { body = JSON.parse(rawText || '{}'); } catch { return sendJson(res, 400, { error: 'invalid JSON body' }); }
  const seq = ++reqSeq;
  fs.writeFileSync(path.join(ARGS.logdir, `req-${seq}.json`), raw, { flag: 'wx' });

  const stream = body.stream === true;
  const auxReason = isStructured(body) ? 'structured' : (state.aux_match.some((s) => rawText.includes(s)) ? 'marker' : null);
  const aux = auxReason !== null;
  const tools = Array.isArray(body.tools) ? body.tools.length : 0;
  let fault;
  let source;
  let tag = null;
  const forced = String(url.searchParams.get('fault') || req.headers['x-mock-fault'] || '').toUpperCase();
  const once = state.once;
  if (FAULTS.has(forced)) { fault = forced; source = 'forced'; }
  else if (once && stream && !(aux && once.skip_aux) && (!once.match || rawText.includes(once.match)) && !once.avoid.some((s) => rawText.includes(s))) {
    fault = once.fault; source = 'once'; tag = once.tag; state.once = null;
  } else { fault = state.always; source = 'always'; }

  const model = typeof body.model === 'string' ? body.model : 'mock-model';
  const assistants = assistantTexts(endpoint, body);
  const meta = {
    seq, instance: INSTANCE, started_ms: startedMs, body_ms: Date.now(), method: req.method, path: p, endpoint, model,
    user_agent: String(req.headers['user-agent'] || ''), fault, fault_source: source, aux, aux_reason: auxReason, tools_count: tools,
    profile: aux ? 'aux' : (fault === 'FLONG' ? 'long' : state.profile), tag_applied: Boolean(tag),
    req_bytes: raw.length, req_sha256: crypto.createHash('sha256').update(raw).digest('hex'),
    req_assistant_messages: assistants.length,
    req_max_tokens: body.max_tokens ?? body.max_output_tokens ?? null,
  };

  if (!stream) {
    if (fault !== 'F0') {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.flushHeaders();
      res.socket.end();
      appendLog({ ...meta, stream: false, first_byte_ms: null, ended_ms: Date.now(), bytes_sent: 0, events_count: 0, events: [], witnesses: {}, ending: 'fin', continuation: null });
      return;
    }
    const cont = aux ? null : continuationDecision(endpoint, body);
    const text = aux ? structuredText() : selectContent('F0', state.profile, null, cont).full.map((x) => `${x}\n`).join('');
    const str = JSON.stringify(nonStreamBody(endpoint, model, text));
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(str);
    appendLog({ ...meta, stream: false, first_byte_ms: Date.now(), ended_ms: Date.now(), bytes_sent: Buffer.byteLength(str), events_count: 0, events: [], witnesses: {}, ending: 'clean', continuation: cont });
    return;
  }

  let actions;
  let cont = null;
  let delay = url.searchParams.has('delay') ? Number(url.searchParams.get('delay')) : ARGS.delay;
  if (aux && fault === 'F0') {
    actions = buildStructuredStream(endpoint, model);
  } else {
    cont = fault === 'F0' ? continuationDecision(endpoint, body) : null;
    const sel = selectContent(fault, aux ? 'short' : state.profile, tag, cont);
    if (sel.prof === 'long' && !url.searchParams.has('delay')) delay = ARGS.longDelay;
    actions = endpoint === 'cc' ? buildCc(model, fault, sel) : endpoint === 'responses' ? buildResponses(model, fault, sel) : buildAnthropic(model, fault, sel);
    if (cont && cont.decision === 'continue') {
      cont.sent_first = sel.full.length ? (sel.full[0].match(/【([PL]\d+)】/) || [null, null])[1] : null;
      cont.sent_last = sel.full.length ? (sel.full[sel.full.length - 1].match(/【([PL]\d+)】/) || [null, null])[1] : null;
      console.log(`[mock] #${seq} continuation: trailing assistant ends at ${cont.trailing_family === 'long' ? 'L' : 'P'}${cont.trailing_max}, sending ${sel.full.length} remaining paragraphs`);
    }
  }
  await runStream(res, actions, { ...meta, continuation: cont, frame_delay_ms: delay }, delay);
});

function shutdown() { server.close(() => process.exit(0)); setTimeout(() => process.exit(0), 1000).unref(); }
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

server.listen(ARGS.port, ARGS.host, () => {
  const port = server.address().port;
  const ready = { port, pid: process.pid, instance: INSTANCE, host: ARGS.host, content_sha256: CONTENT_SHA256, continuation: ARGS.continuation, delay_ms: ARGS.delay, long_delay_ms: ARGS.longDelay };
  if (ARGS.readyFile) {
    const tmp = `${ARGS.readyFile}.tmp-${process.pid}`;
    fs.writeFileSync(tmp, JSON.stringify(ready));
    fs.renameSync(tmp, ARGS.readyFile);
  }
  console.log(`[mock] ready ${JSON.stringify(ready)}`);
});
