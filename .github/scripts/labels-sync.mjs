#!/usr/bin/env node

import assert from "node:assert/strict";
import { appendFile, readFile } from "node:fs/promises";
import process from "node:process";
import { pathToFileURL } from "node:url";

const EXPECTED_SCHEMA_VERSION = 2;
const DEFAULT_MANIFEST = ".github/labels.json";
const API_VERSION = "2022-11-28";
const LABELS_PER_PAGE = 100;
const MAX_LABEL_PAGES = 100;
const MAX_RATE_LIMIT_RETRIES = 2;
export const MAX_RETRY_DELAY_MS = 5000;

export function compareNames(left, right) {
  const leftKey = left.toLowerCase();
  const rightKey = right.toLowerCase();
  if (leftKey < rightKey) return -1;
  if (leftKey > rightKey) return 1;
  return left < right ? -1 : left > right ? 1 : 0;
}

function sameKeys(value, expected) {
  const actual = Object.keys(value).sort();
  return JSON.stringify(actual) === JSON.stringify([...expected].sort());
}

export function normalizedLiveLabel(label) {
  return {
    name: String(label.name ?? ""),
    color: String(label.color ?? "").toUpperCase(),
    description: label.description == null ? "" : String(label.description)
  };
}

function validateLabelArray(labels, location, seen) {
  const errors = [];
  if (!Array.isArray(labels)) return [`${location} must be an array`];

  labels.forEach((label, index) => {
    const item = `${location}[${index}]`;
    if (!label || typeof label !== "object" || Array.isArray(label)) {
      errors.push(`${item} must be an object`);
      return;
    }
    if (!sameKeys(label, ["name", "color", "description"])) {
      errors.push(`${item} must contain exactly name, color, and description`);
    }

    if (typeof label.name !== "string") {
      errors.push(`${item}.name must be a string`);
    } else {
      if (label.name.length === 0 || label.name !== label.name.trim()) {
        errors.push(`${item}.name must be non-empty with no surrounding whitespace`);
      }
      if (label.name.length > 50) errors.push(`${item}.name exceeds GitHub's 50-character limit`);
      if (/\r|\n/.test(label.name)) errors.push(`${item}.name must be single-line`);
      const key = label.name.toLowerCase();
      if (seen.has(key)) {
        errors.push(`${item}.name duplicates ${seen.get(key)} case-insensitively`);
      } else {
        seen.set(key, `${item}.name`);
      }
    }

    if (typeof label.color !== "string" || !/^[0-9A-F]{6}$/.test(label.color)) {
      errors.push(`${item}.color must be six uppercase hexadecimal characters without #`);
    }
    if (typeof label.description !== "string") {
      errors.push(`${item}.description must be a string`);
    } else {
      if (label.description.length === 0) errors.push(`${item}.description must not be empty`);
      if (label.description.length > 100) errors.push(`${item}.description exceeds GitHub's 100-character limit`);
      if (/\r|\n/.test(label.description)) errors.push(`${item}.description must be single-line`);
    }
  });

  for (let index = 1; index < labels.length; index += 1) {
    const previous = labels[index - 1]?.name;
    const current = labels[index]?.name;
    if (typeof previous === "string" && typeof current === "string" && compareNames(previous, current) >= 0) {
      errors.push(`${location} must be sorted case-insensitively by name: ${previous} precedes ${current}`);
      break;
    }
  }
  return errors;
}

export function validateManifest(document) {
  const errors = [];
  if (!document || typeof document !== "object" || Array.isArray(document)) {
    throw new Error("Manifest must be a JSON object.");
  }
  if (!sameKeys(document, ["schema_version", "prune", "labels"])) {
    errors.push("root must contain exactly schema_version, prune, and labels");
  }
  if (document.schema_version !== EXPECTED_SCHEMA_VERSION) {
    errors.push(`schema_version must be ${EXPECTED_SCHEMA_VERSION}`);
  }
  if (typeof document.prune !== "boolean") errors.push("prune must be a boolean");

  errors.push(...validateLabelArray(document.labels, "labels", new Map()));
  if (Array.isArray(document.labels) && document.labels.length === 0) errors.push("labels must not be empty");

  if (errors.length > 0) throw new Error(`Invalid label manifest:\n- ${errors.join("\n- ")}`);
  return structuredClone(document);
}

export function resolveDesired(document) {
  const labels = [...validateManifest(document).labels];
  labels.sort((left, right) => compareNames(left.name, right.name));
  return labels;
}

export function planChanges(desiredLabels, liveLabels, { prune = true } = {}) {
  const desired = new Map(desiredLabels.map(label => [label.name.toLowerCase(), label]));
  const live = new Map(liveLabels.map(label => {
    const normalized = normalizedLiveLabel(label);
    return [normalized.name.toLowerCase(), normalized];
  }));
  const changes = [];

  for (const [key, target] of desired) {
    const current = live.get(key);
    if (!current) {
      changes.push({ action: "create", name: target.name, target });
      continue;
    }
    const fields = [];
    if (current.name !== target.name) fields.push("name");
    if (current.color !== target.color) fields.push("color");
    if (current.description !== target.description) fields.push("description");
    if (fields.length > 0) {
      changes.push({ action: "update", name: target.name, currentName: current.name, fields, target });
    }
  }

  if (prune) {
    for (const [key, current] of live) {
      if (!desired.has(key)) changes.push({ action: "delete", name: current.name, currentName: current.name });
    }
  }

  const order = { update: 0, create: 1, delete: 2 };
  changes.sort((left, right) => order[left.action] - order[right.action] || compareNames(left.name, right.name));
  return changes;
}

function parseArguments(argv) {
  const parsed = {
    manifest: DEFAULT_MANIFEST,
    mode: null,
    live: null,
    repository: process.env.GITHUB_REPOSITORY || null,
    dryRun: false,
    selfTest: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--dry-run") {
      parsed.dryRun = true;
    } else if (argument === "--self-test") {
      parsed.selfTest = true;
    } else if (["--manifest", "--mode", "--live", "--repository"].includes(argument)) {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`${argument} requires a value`);
      parsed[argument.slice(2)] = value;
      index += 1;
    } else {
      throw new Error(`Unknown argument: ${argument}`);
    }
  }
  return parsed;
}

export async function loadJson(path) {
  let text;
  try {
    text = await readFile(path, "utf8");
  } catch (error) {
    throw new Error(`Cannot read ${path}: ${error.message}`);
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error.message}`);
  }
}

function splitRepository(repository) {
  const parts = String(repository ?? "").split("/");
  if (parts.length !== 2 || parts.some(part => part.length === 0)) {
    throw new Error("repository must be in owner/name form");
  }
  return parts.map(encodeURIComponent);
}

function apiUrl(repository, suffix) {
  const [owner, repo] = splitRepository(repository);
  // The runner sets GITHUB_API_URL, which differs from api.github.com on GitHub Enterprise.
  const base = (process.env.GITHUB_API_URL || "https://api.github.com").replace(/\/+$/, "");
  return `${base}/repos/${owner}/${repo}${suffix}`;
}

function sleep(milliseconds) {
  return new Promise(resolve => setTimeout(resolve, milliseconds));
}

function isRateLimited(response) {
  return response.status === 429
    || (
      response.status === 403
      && (
        response.headers.get("x-ratelimit-remaining") === "0"
        || response.headers.has("retry-after")
      )
    );
}

export function retryDelayMs(response, attempt) {
  const header = response.headers.get("retry-after");
  const retryAfter = header !== null && header.trim() !== "" ? Number(header) : NaN;
  if (Number.isFinite(retryAfter) && retryAfter >= 0) {
    return Math.min(retryAfter * 1000, MAX_RETRY_DELAY_MS);
  }
  return Math.min(1000 * (2 ** attempt), MAX_RETRY_DELAY_MS);
}

async function githubRequest(repository, token, method, suffix, body) {
  for (let attempt = 0; ; attempt += 1) {
    const response = await fetch(apiUrl(repository, suffix), {
      method,
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "k-risk-engines-labels-sync"
      },
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    if (response.ok) {
      if (response.status === 204) return null;
      return response.json();
    }

    const detail = await response.text();
    const retryable = method === "GET" && isRateLimited(response);
    if (!retryable || attempt >= MAX_RATE_LIMIT_RETRIES) {
      throw new Error(`${method} ${suffix} failed with HTTP ${response.status}: ${detail.slice(0, 500)}`);
    }
    await sleep(retryDelayMs(response, attempt));
  }
}

export async function listLiveLabels(repository, token) {
  const labels = [];
  for (let page = 1; page <= MAX_LABEL_PAGES; page += 1) {
    const batch = await githubRequest(
      repository,
      token,
      "GET",
      `/labels?per_page=${LABELS_PER_PAGE}&page=${page}`
    );
    if (!Array.isArray(batch)) throw new Error("GitHub labels response is not an array");
    labels.push(...batch.map(normalizedLiveLabel));
    if (batch.length < LABELS_PER_PAGE) return labels;
  }
  throw new Error(`GitHub label pagination exceeded ${MAX_LABEL_PAGES} pages`);
}

// The issues endpoint covers pull requests; state=all adds closed items.
export const USAGE_SAMPLE = 10;
const ISSUES_PER_PAGE = 100;
const MAX_ISSUE_PAGES = 100;

// The issues, pull requests included, that carry the label: at most
// USAGE_SAMPLE numbers in ascending order, and whether more exist. The labels
// filter is a comma-separated list, so a name with a comma cannot be queried:
// every issue and pull request in every state is scanned and its labels are
// compared literally. A malformed response or an exhausted page limit throws,
// so that an unproved absence never allows a prune.
export async function labelUsage(repository, token, name) {
  if (!name.includes(",")) {
    const batch = await githubRequest(
      repository,
      token,
      "GET",
      `/issues?state=all&per_page=${USAGE_SAMPLE + 1}&labels=${encodeURIComponent(name)}`
    );
    if (!Array.isArray(batch)) throw new Error("GitHub issues response is not an array");
    return sampleUsage(batch.map(issue => issue.number));
  }
  const numbers = [];
  for (let page = 1; page <= MAX_ISSUE_PAGES; page += 1) {
    const batch = await githubRequest(
      repository,
      token,
      "GET",
      `/issues?state=all&per_page=${ISSUES_PER_PAGE}&page=${page}`
    );
    if (!Array.isArray(batch)) throw new Error("GitHub issues response is not an array");
    for (const issue of batch) {
      if (!Array.isArray(issue.labels)) throw new Error("GitHub issue has no labels array");
      if (issue.labels.some(label => (typeof label === "string" ? label : label?.name) === name)) {
        numbers.push(issue.number);
      }
    }
    if (batch.length < ISSUES_PER_PAGE) return sampleUsage(numbers);
  }
  throw new Error(`GitHub issue pagination exceeded ${MAX_ISSUE_PAGES} pages while checking ${JSON.stringify(name)}`);
}

export function sampleUsage(numbers) {
  const sorted = [...numbers].sort((left, right) => left - right);
  return { numbers: sorted.slice(0, USAGE_SAMPLE), more: sorted.length > USAGE_SAMPLE };
}

// The deletions that would remove a label from an issue or pull request.
export async function findBlockedDeletions(changes, usageOf) {
  const blocked = [];
  for (const change of changes) {
    if (change.action !== "delete") continue;
    const usage = await usageOf(change.currentName);
    if (usage.numbers.length > 0) {
      blocked.push({ name: change.currentName, numbers: usage.numbers, more: usage.more });
    }
  }
  return blocked;
}

export function describeUsage({ numbers, more }) {
  return `${numbers.map(number => `#${number}`).join(", ")}${more ? " and others" : ""}`;
}

// Deleting a label removes it from every issue and pull request, closed ones
// included, and cannot be undone: refuse before any change is applied.
export async function assertSafeDeletions(changes, usageOf) {
  const blocked = await findBlockedDeletions(changes, usageOf);
  if (blocked.length > 0) {
    const listed = blocked.map(item => `${JSON.stringify(item.name)} (${describeUsage(item)})`).join(", ");
    throw new Error(
      `Refusing to prune labels still used by an issue or pull request: ${listed}. No change was applied. `
      + "Remove each label from its issues and pull requests, or add it to the manifest."
    );
  }
}

async function applyChanges(repository, token, changes) {
  for (const change of changes) {
    if (change.action === "update") {
      await githubRequest(repository, token, "PATCH", `/labels/${encodeURIComponent(change.currentName)}`, {
        new_name: change.target.name,
        color: change.target.color,
        description: change.target.description
      });
    } else if (change.action === "create") {
      await githubRequest(repository, token, "POST", "/labels", change.target);
    } else if (change.action === "delete") {
      await githubRequest(repository, token, "DELETE", `/labels/${encodeURIComponent(change.currentName)}`);
    }
  }
}

function singleLine(value) {
  return String(value).replace(/\r\n?|\n/g, " ");
}

// Plain text in a table cell: one line, with pipes escaped.
export function markdownEscape(value) {
  return singleLine(value).replaceAll("|", "\\|");
}

// A code span that the value cannot close: its delimiter is longer than any
// run of backticks in the value. In a table cell, pipes are escaped as well.
export function inlineCode(value, { table = false } = {}) {
  let text = singleLine(value);
  if (table) text = text.replaceAll("|", "\\|");
  const longest = Math.max(0, ...(text.match(/`+/g) ?? []).map(run => run.length));
  const fence = "`".repeat(longest + 1);
  const padding = /^[` ]|[` ]$/.test(text) ? " " : "";
  return `${fence}${padding}${text}${padding}${fence}`;
}

function renderLabelNames(labels) {
  if (labels.length === 0) return "none";
  return labels.map(label => inlineCode(label.name)).join(", ");
}

function renderSummary({
  mode,
  manifest,
  manifestPath,
  desiredLabels,
  changes = [],
  verified = null,
  dryRun = false,
  blocked = null,
  error = null,
  partial = false
}) {
  const resolvedLabels = desiredLabels ?? [];
  const planned = changes !== null;
  const counts = Object.fromEntries(["create", "update", "delete"].map(action => [
    action,
    planned ? changes.filter(change => change.action === action).length : "n/a"
  ]));
  const lines = [
    "# Repository label synchronization",
    "",
    `- Mode: ${inlineCode(mode)}${dryRun ? " (dry run)" : ""}`,
    `- Label manifest: ${inlineCode(manifestPath ?? "unavailable")}`,
    `- Schema: **${manifest?.schema_version ?? "unavailable"}**`,
    `- Labels: **${resolvedLabels.length}**`,
    `- Prune: **${manifest ? (manifest.prune ? "enabled" : "disabled") : "unavailable"}**`,
    `- Planned changes: **${planned ? changes.length : "not computed (live labels not read)"}**`,
    `- Create / update / delete: **${counts.create} / ${counts.update} / ${counts.delete}**`
  ];
  if (blocked !== null) lines.push(`- Deletions blocked by labels in use: **${blocked.length}**`);
  if (verified !== null) lines.push(`- Post-run exact match: **${verified ? "yes" : "no"}**`);
  lines.push(
    "",
    "## Label catalogue",
    "",
    `- Labels (${resolvedLabels.length}): ${renderLabelNames(resolvedLabels)}`
  );
  if (error) {
    lines.push("", "## Failure", "", inlineCode(error));
    if (partial) {
      lines.push("", "The failure happened during or after reconciliation: some changes may already be applied. Compare the live labels with the manifest.");
    }
  } else if (!planned) {
    lines.push("", "Live labels were not read; no changes were planned.");
  } else if (changes.length === 0) {
    lines.push("", "No label changes are required.");
  } else {
    lines.push("", "| Action | Label | Detail |", "|---|---|---|");
    for (const change of changes) {
      const used = change.action === "delete" ? (blocked ?? []).find(item => item.name === change.currentName) : undefined;
      const detail = change.action === "update" ? change.fields.join(", ")
        : used ? `outside the manifest; blocked, used by ${describeUsage(used)}`
          : change.action === "delete" ? "outside the manifest" : "missing live label";
      lines.push(`| ${change.action} | ${inlineCode(change.name, { table: true })} | ${markdownEscape(detail)} |`);
    }
  }
  return `${lines.join("\n")}\n`;
}

async function publishSummary(summary) {
  process.stdout.write(summary);
  if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY, summary, "utf8");
}

function expectFailure(operation, pattern) {
  assert.throws(operation, pattern);
}

async function runSelfTest(manifestPath) {
  for (const [header, attempt, expected] of [
    [null, 0, 1000], [null, 2, 4000], ["", 1, 2000],
    ["invalid", 1, 2000], ["-1", 1, 2000], ["0", 2, 0],
    ["2", 0, 2000], ["999999", 0, MAX_RETRY_DELAY_MS],
    [null, 20, MAX_RETRY_DELAY_MS]
  ]) {
    const headers = new Headers(header === null ? {} : { "retry-after": header });
    assert.equal(retryDelayMs({ headers }, attempt), expected, `Retry-After: ${header}`);
  }

  const baseline = await loadJson(manifestPath);
  const manifest = validateManifest(baseline);
  const desired = resolveDesired(manifest);

  const missingRoot = structuredClone(baseline);
  delete missingRoot.prune;
  expectFailure(() => validateManifest(missingRoot), /root must contain exactly/);

  const extraRoot = structuredClone(baseline);
  extraRoot.overlays = {};
  expectFailure(() => validateManifest(extraRoot), /root must contain exactly/);

  const wrongSchema = structuredClone(baseline);
  wrongSchema.schema_version = 1;
  expectFailure(() => validateManifest(wrongSchema), /schema_version/);

  const invalidPrune = structuredClone(baseline);
  invalidPrune.prune = "true";
  expectFailure(() => validateManifest(invalidPrune), /prune must be a boolean/);

  const emptyLabels = structuredClone(baseline);
  emptyLabels.labels = [];
  expectFailure(() => validateManifest(emptyLabels), /must not be empty/);

  const missingField = structuredClone(baseline);
  delete missingField.labels[0].description;
  expectFailure(() => validateManifest(missingField), /name, color, and description/);

  const invalidColor = structuredClone(baseline);
  invalidColor.labels[0].color = "#c24e00";
  expectFailure(() => validateManifest(invalidColor), /uppercase hexadecimal/);

  const duplicateName = structuredClone(baseline);
  duplicateName.labels[1].name = baseline.labels[0].name.toUpperCase();
  expectFailure(() => validateManifest(duplicateName), /duplicates/);

  const longDescription = structuredClone(baseline);
  longDescription.labels[0].description = "x".repeat(101);
  expectFailure(() => validateManifest(longDescription), /100-character/);

  const unsorted = structuredClone(baseline);
  [unsorted.labels[0], unsorted.labels[1]] = [unsorted.labels[1], unsorted.labels[0]];
  expectFailure(() => validateManifest(unsorted), /sorted/);

  assert.equal(planChanges(desired, desired, { prune: manifest.prune }).length, 0, "idempotent plan must be empty");

  assert.deepEqual(planChanges(desired, desired.slice(1)).map(change => change.action), ["create"]);

  const changed = structuredClone(desired);
  changed[0].color = "000000";
  changed[0].description = "changed";
  const changedPlan = planChanges(desired, changed);
  assert.deepEqual(changedPlan.map(change => change.action), ["update"]);
  assert.deepEqual(changedPlan[0].fields, ["color", "description"]);

  const extra = [...structuredClone(desired), { name: "extra", color: "ABCDEF", description: "extra" }];
  assert.deepEqual(planChanges(desired, extra, { prune: true }).map(change => change.action), ["delete"]);
  assert.equal(planChanges(desired, extra, { prune: false }).length, 0);

  const caseDrift = structuredClone(desired);
  caseDrift[0].name = desired[0].name.toUpperCase();
  assert.deepEqual(planChanges(desired, caseDrift)[0].fields, ["name"]);

  const summary = renderSummary({
    mode: "plan",
    manifest,
    manifestPath: "fixture-labels.json",
    desiredLabels: desired,
    dryRun: true
  });
  assert.match(summary, /Label manifest: `fixture-labels\.json`/);
  assert.match(summary, new RegExp(`Labels: \\*\\*${desired.length}\\*\\*`));
  const validateSummary = renderSummary({
    mode: "validate",
    manifest,
    manifestPath: "fixture-labels.json",
    desiredLabels: desired,
    changes: null
  });
  assert.match(validateSummary, /Planned changes: \*\*not computed \(live labels not read\)\*\*/);
  assert.match(validateSummary, /Live labels were not read; no changes were planned\./);
  assert.doesNotMatch(validateSummary, /No label changes are required/);
  const failureSummary = renderSummary({
    mode: "failed",
    manifest: null,
    manifestPath: null,
    desiredLabels: [],
    changes: [{ action: "create", name: "new" }],
    partial: true,
    error: "write failed"
  });
  assert.match(failureSummary, /Prune: \*\*unavailable\*\*/);
  assert.match(failureSummary, /Planned changes: \*\*1\*\*/);
  assert.match(failureSummary, /some changes may already be applied/);
  assert.match(summary, new RegExp(`Labels \\(${desired.length}\\):`));
  for (const label of desired) assert.ok(summary.includes(inlineCode(label.name)), label.name);

  // Values are data: no backtick, pipe or line break may close the code span or split the row.
  assert.equal(inlineCode("plain"), "`plain`");
  assert.equal(inlineCode("wip `x`"), "`` wip `x` ``");
  assert.equal(inlineCode("a ``b`` c"), "```a ``b`` c```");
  assert.equal(inlineCode("`edge"), "`` `edge ``");
  assert.equal(inlineCode("a|b"), "`a|b`");
  assert.equal(inlineCode("a|b", { table: true }), "`a\\|b`");
  assert.equal(inlineCode("one\r\ntwo\rthree\nfour"), "`one two three four`");
  assert.equal(markdownEscape("x|y\r\nz"), "x\\|y z");
  const special = [{ name: "wip `x`", color: "ABCDEF", description: "d" },
    { name: "needs|triage", color: "ABCDEF", description: "d" }];
  const specialSummary = renderSummary({
    mode: "plan",
    manifest,
    manifestPath: "fixture-labels.json",
    desiredLabels: desired,
    changes: planChanges(desired, [...structuredClone(desired), ...special])
  });
  assert.ok(specialSummary.includes("| delete | `` wip `x` `` | outside the manifest |"), specialSummary);
  assert.ok(specialSummary.includes("| delete | `needs\\|triage` | outside the manifest |"), specialSummary);
  const errorSummary = renderSummary({
    mode: "failed",
    manifest,
    manifestPath: "fixture-labels.json",
    desiredLabels: desired,
    changes: null,
    error: "HTTP 422: {\"message\":\"`bad`\"}\r\nnext line"
  });
  assert.ok(errorSummary.includes("``HTTP 422: {\"message\":\"`bad`\"} next line``"), errorSummary);
  assert.doesNotMatch(errorSummary, /\r/);

  // Pruning refuses labels in use before any change, and says which issues and pull requests use them.
  const asked = [];
  const usage = used => async name => {
    asked.push(name);
    return used[name] ?? { numbers: [], more: false };
  };
  const pruned = planChanges(desired, [...structuredClone(desired),
    { name: "unused", color: "ABCDEF", description: "d" },
    { name: "in-use", color: "ABCDEF", description: "d" },
    { name: "a,b", color: "ABCDEF", description: "d" }]);
  const inUse = { "in-use": { numbers: [3, 7], more: false }, "a,b": { numbers: [9], more: true } };
  await assert.rejects(assertSafeDeletions(pruned, usage(inUse)),
    error => /still used by an issue or pull request: "a,b" \(#9 and others\), "in-use" \(#3, #7\)/.test(error.message)
      && /No change was applied/.test(error.message));
  assert.deepEqual(asked, ["a,b", "in-use", "unused"], "every deleted label is checked, a comma name included");
  asked.length = 0;
  await assertSafeDeletions(planChanges(desired, [...structuredClone(desired),
    { name: "unused", color: "ABCDEF", description: "d" }, { name: "x,y", color: "ABCDEF", description: "d" }]), usage({}));
  assert.deepEqual(asked, ["unused", "x,y"], "an unused comma name is allowed once its absence is proved");
  asked.length = 0;
  await assertSafeDeletions(planChanges(desired, desired.slice(1)), usage({ anything: { numbers: [1], more: false } }));
  assert.deepEqual(asked, [], "a plan without deletions makes no query");

  // The dry-run preview reads every use, marks each blocked deletion and refuses nothing.
  const blocked = await findBlockedDeletions(pruned, usage(inUse));
  assert.deepEqual(blocked, [
    { name: "a,b", numbers: [9], more: true },
    { name: "in-use", numbers: [3, 7], more: false }]);
  const previewSummary = renderSummary({
    mode: "reconcile", manifest, manifestPath: "fixture-labels.json", desiredLabels: desired,
    changes: pruned, dryRun: true, blocked
  });
  assert.ok(previewSummary.includes("- Deletions blocked by labels in use: **2**"), previewSummary);
  assert.ok(previewSummary.includes("| delete | `in-use` | outside the manifest; blocked, used by #3, #7 |"), previewSummary);
  assert.ok(previewSummary.includes("| delete | `a,b` | outside the manifest; blocked, used by #9 and others |"), previewSummary);
  assert.ok(previewSummary.includes("| delete | `unused` | outside the manifest |"), previewSummary);

  // Reading uses: a sample of ten in ascending order, and a literal scan for a name with a comma.
  assert.deepEqual(sampleUsage([5, 1, 3]), { numbers: [1, 3, 5], more: false });
  assert.deepEqual(sampleUsage([12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]),
    { numbers: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], more: true });
  const issuesFetch = items => async url => {
    const target = new URL(url);
    const perPage = Number(target.searchParams.get("per_page"));
    const page = Number(target.searchParams.get("page") ?? 1);
    const filter = target.searchParams.get("labels");
    const rows = filter === null ? items : items.filter(item => item.labels.some(label => label.name === filter));
    return { ok: true, status: 200, json: async () => rows.slice((page - 1) * perPage, page * perPage) };
  };
  const tagged = (number, ...names) => ({ number, labels: names.map(name => ({ name })) });
  const items = [...Array.from({ length: 250 }, (_, index) => tagged(index + 1, "other")),
    tagged(251, "a,b"), tagged(130, "a,b", "other"), tagged(252, "a"), tagged(253, "b")];
  const realFetch = globalThis.fetch;
  try {
    globalThis.fetch = issuesFetch(items);
    assert.deepEqual(await labelUsage("o/r", "t", "a,b"), { numbers: [130, 251], more: false });
    assert.deepEqual(await labelUsage("o/r", "t", "a,c"), { numbers: [], more: false },
      "a comma name with no use is proved unused by the scan");
    assert.deepEqual(await labelUsage("o/r", "t", "a"), { numbers: [252], more: false });
    globalThis.fetch = issuesFetch(Array.from({ length: 12 }, (_, index) => tagged(index + 1, "busy")));
    assert.deepEqual(await labelUsage("o/r", "t", "busy"),
      { numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], more: true });
    globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => ({ message: "odd" }) });
    await assert.rejects(labelUsage("o/r", "t", "a,b"), /not an array/);
    await assert.rejects(labelUsage("o/r", "t", "plain"), /not an array/);
    globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => [{ number: 1 }] });
    await assert.rejects(labelUsage("o/r", "t", "a,b"), /no labels array/);
    globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => Array.from({ length: 100 }, () => tagged(1, "other")) });
    await assert.rejects(labelUsage("o/r", "t", "a,b"), /pagination exceeded/);
  } finally {
    globalThis.fetch = realFetch;
  }

  process.stdout.write("SELF-TEST PASS: retry delays, validation, reconciliation, safe pruning and summary fixtures\n");
}

// What the run knew before a failure, so that the failure summary reports it.
const runState = { summaryBase: null, changes: null, applying: false, verified: null };

async function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.selfTest) {
    await runSelfTest(options.manifest);
    return;
  }

  const manifest = validateManifest(await loadJson(options.manifest));
  const desired = resolveDesired(manifest);
  const summaryBase = {
    manifest,
    manifestPath: options.manifest,
    desiredLabels: desired
  };
  runState.summaryBase = summaryBase;

  if (options.mode === "validate") {
    await publishSummary(renderSummary({ mode: "validate", ...summaryBase, changes: null }));
    return;
  }

  let live;
  if (options.mode === "plan") {
    if (!options.live) throw new Error("--mode plan requires --live");
    const liveDocument = await loadJson(options.live);
    live = Array.isArray(liveDocument) ? liveDocument : liveDocument.labels;
    if (!Array.isArray(live)) throw new Error("live fixture must be an array or contain a labels array");
  } else if (options.mode === "reconcile") {
    if (!options.repository) throw new Error("--mode reconcile requires --repository or GITHUB_REPOSITORY");
    if (!process.env.GITHUB_TOKEN) throw new Error("--mode reconcile requires GITHUB_TOKEN");
    live = await listLiveLabels(options.repository, process.env.GITHUB_TOKEN);
  } else {
    throw new Error("--mode must be validate, plan, or reconcile");
  }

  const changes = planChanges(desired, live, { prune: manifest.prune });
  runState.changes = changes;
  const usageOf = name => labelUsage(options.repository, process.env.GITHUB_TOKEN, name);
  if (options.mode === "reconcile" && options.dryRun) {
    // The preview reads every use, marks each blocked deletion and changes nothing.
    const blocked = await findBlockedDeletions(changes, usageOf);
    await publishSummary(renderSummary({ mode: options.mode, ...summaryBase, changes, dryRun: true, blocked }));
    return;
  }
  if (options.mode === "reconcile") {
    await assertSafeDeletions(changes, usageOf);
  }
  if (options.mode === "plan" || options.dryRun) {
    await publishSummary(renderSummary({ mode: options.mode, ...summaryBase, changes, dryRun: options.dryRun }));
    return;
  }

  runState.applying = true;
  await applyChanges(options.repository, process.env.GITHUB_TOKEN, changes);
  const after = await listLiveLabels(options.repository, process.env.GITHUB_TOKEN);
  const remaining = planChanges(desired, after, { prune: manifest.prune });
  const verified = remaining.length === 0;
  if (!verified) {
    runState.verified = false;
    throw new Error(`Post-run verification found ${remaining.length} remaining difference(s)`);
  }
  await publishSummary(renderSummary({ mode: "reconcile", ...summaryBase, changes, verified }));
}

// Run only when executed directly, so that labels-drift.mjs can import the planner.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(async error => {
    const message = error instanceof Error ? error.message : String(error);
    try {
      await publishSummary(renderSummary({
        mode: "failed",
        ...(runState.summaryBase ?? {
          manifest: null,
          manifestPath: null,
          desiredLabels: []
        }),
        changes: runState.changes,
        verified: runState.verified,
        partial: runState.applying,
        error: message
      }));
    } finally {
      process.stderr.write(`${message}\n`);
      process.exitCode = 1;
    }
  });
}
