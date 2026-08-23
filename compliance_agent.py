#!/usr/bin/env python3
"""
Compliance Memory Agent
=======================
Stateful compliance reviewer for Spring Boot + Oracle DB repos.
Remembers every past scan, summarises trends, then reviews today's diff.

Model-agnostic via LiteLLM — configure once via env var, works with:
  Claude (Anthropic)  →  LLM_MODEL=claude-opus-4-5
  GPT-4o (OpenAI)     →  LLM_MODEL=gpt-4o
  GitHub Copilot      →  LLM_MODEL=azure/gpt-4o  (set AZURE_* vars)
  Codex               →  LLM_MODEL=openai/gpt-3.5-turbo
  Gemini              →  LLM_MODEL=gemini/gemini-1.5-pro
"""

import os
import json
import sys
import subprocess
import yaml
from datetime import datetime, timezone
from pathlib import Path

import litellm

litellm.suppress_debug_info = True   # clean console output

# ── Paths ──────────────────────────────────────────────────────────────────────
MEMORY_DIR   = Path(".compliance-memory")
RUNS_DIR     = MEMORY_DIR / "runs"
SUMMARY_FILE = MEMORY_DIR / "summary.md"
RULES_FILE   = MEMORY_DIR / "compliance-rules.yaml"

# ── Model config ───────────────────────────────────────────────────────────────
# Override LLM_MODEL to switch providers — no code changes needed.
# LiteLLM picks up provider API keys from env automatically:
#   ANTHROPIC_API_KEY   → Claude models
#   OPENAI_API_KEY      → OpenAI / Codex
#   AZURE_API_KEY + AZURE_API_BASE + AZURE_API_VERSION → Azure / Copilot
#   GEMINI_API_KEY      → Google Gemini
MODEL      = os.getenv("LLM_MODEL", "claude-opus-4-5")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# Set to "true" to exit with code 1 on any HIGH finding (blocks CI merge)
FAIL_ON_HIGH = os.getenv("COMPLIANCE_FAIL_ON_HIGH", "false").lower() == "true"


# ── LLM helper ────────────────────────────────────────────────────────────────

def llm_call(system: str, user: str) -> str:
    """Single LLM call via LiteLLM. Model-agnostic."""
    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content.strip()


# ── Git helpers ────────────────────────────────────────────────────────────────

def run_git(*args) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    return result.stdout.strip()


def get_git_diff() -> str:
    """Diff of the last commit, Java files only."""
    diff = run_git("diff", "HEAD~1", "HEAD", "--unified=5",
                   "--diff-filter=ACM", "--", "*.java")
    if not diff:
        # First commit or single-commit repo
        diff = run_git("show", "--unified=5", "HEAD", "--", "*.java")
    return diff or "(no Java file changes detected in this commit)"


def get_commit_info() -> dict:
    return {
        "hash":    run_git("rev-parse", "--short", "HEAD"),
        "branch":  run_git("rev-parse", "--abbrev-ref", "HEAD"),
        "message": run_git("log", "-1", "--pretty=%s"),
        "author":  run_git("log", "-1", "--pretty=%an"),
        "date":    run_git("log", "-1", "--pretty=%ci"),
    }


# ── Memory helpers ─────────────────────────────────────────────────────────────

def load_rules() -> str:
    if RULES_FILE.exists():
        with open(RULES_FILE) as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, default_flow_style=False)
    return "(compliance-rules.yaml not found — place it at .compliance-memory/compliance-rules.yaml)"


def load_all_runs() -> list:
    if not RUNS_DIR.exists():
        return []
    runs = []
    for f in sorted(RUNS_DIR.glob("*.json")):
        try:
            with open(f) as fp:
                runs.append(json.load(fp))
        except json.JSONDecodeError:
            pass  # skip corrupt runs
    return runs


def save_run(data: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    data["run_id"] = run_id
    path = RUNS_DIR / f"{run_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def write_summary(text: str):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_FILE, "w") as f:
        f.write(f"# Compliance History Summary\n")
        f.write(f"_Last updated: {datetime.now(timezone.utc).isoformat()}_\n\n")
        f.write(text)


# ── Phase 1 — Summarise all previous runs ─────────────────────────────────────

def phase1_summarise_history(runs: list) -> str:
    if not runs:
        return "No previous runs. This is the first compliance scan for this repo."

    # Feed at most the last 20 runs to stay within context limits
    recent = runs[-20:]
    runs_json = json.dumps(recent, indent=2)

    system = """You are a compliance trend analyst for Java Spring Boot codebases.
You receive a JSON array of past compliance scan results.

Return a structured Markdown summary (under 400 words) covering:
1. Total runs and date range
2. Recurring unresolved findings — rule ID, file, how many times seen
3. Findings resolved between runs — what improved
4. Overall trend: IMPROVING / STABLE / DEGRADING (with brief reason)
5. Top 3 risk areas right now

Be factual and concise. No filler prose."""

    user = f"Past compliance scans ({len(recent)} most recent):\n\n```json\n{runs_json}\n```"

    return llm_call(system, user)


# ── Phase 2 — Run today's compliance scan ─────────────────────────────────────

def phase2_review(diff: str, rules: str, history_summary: str, commit: dict) -> dict:
    system = f"""You are a senior security and compliance engineer reviewing a Java Spring Boot + Oracle DB repo.

COMPLIANCE RULES:
{rules}

HISTORY CONTEXT (from all previous scans):
{history_summary}

Review the git diff below. Return ONLY a valid JSON object with this exact shape — no markdown fences, no prose:
{{
  "findings": [
    {{
      "severity": "HIGH|MEDIUM|LOW",
      "rule": "RULE_ID",
      "file": "path/to/File.java",
      "line": 42,
      "description": "specific description of the violation",
      "recommendation": "exact fix",
      "resolved": false
    }}
  ],
  "summary": "one-paragraph plain English summary of this scan",
  "vs_previous": "what changed vs the last scan — new findings, resolved findings, or no change",
  "trend": "IMPROVING|STABLE|DEGRADING"
}}

If there are no findings, return an empty findings array. Return only valid JSON."""

    # Cap diff at 12 000 chars to stay comfortably within all model context windows
    diff_excerpt = diff[:12000]
    if len(diff) > 12000:
        diff_excerpt += f"\n\n... (diff truncated — {len(diff) - 12000} chars omitted)"

    user = f"""Commit: {commit['hash']} on branch '{commit['branch']}'
Author:  {commit['author']}
Date:    {commit['date']}
Message: {commit['message']}

Git diff:
{diff_excerpt}"""

    raw = llm_call(system, user)

    # Strip markdown fences if the model adds them despite instructions
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("`").strip()

    return json.loads(raw)


# ── Report printer ─────────────────────────────────────────────────────────────

SEVERITY_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

def print_report(commit: dict, result: dict, run_path: Path):
    findings = result.get("findings", [])
    high   = [f for f in findings if f["severity"] == "HIGH"]
    medium = [f for f in findings if f["severity"] == "MEDIUM"]
    low    = [f for f in findings if f["severity"] == "LOW"]

    bar = "─" * 62
    print(f"\n{bar}")
    print(f"  COMPLIANCE REPORT  ·  {commit['hash']}  ·  {commit['branch']}")
    print(bar)
    print(f"  Model   : {MODEL}")
    print(f"  🔴 HIGH   : {len(high)}")
    print(f"  🟡 MEDIUM : {len(medium)}")
    print(f"  🟢 LOW    : {len(low)}")
    print(f"  Trend   : {result.get('trend', 'N/A')}")
    print()

    if findings:
        for f in sorted(findings, key=lambda x: ["HIGH","MEDIUM","LOW"].index(x["severity"])):
            icon = SEVERITY_ICON.get(f["severity"], "⚪")
            print(f"  {icon} [{f['severity']}] {f['rule']}")
            print(f"     File : {f.get('file','?')}  line {f.get('line','?')}")
            print(f"     Issue: {f['description']}")
            print(f"     Fix  : {f['recommendation']}")
            print()
    else:
        print("  ✅ No findings.\n")

    print(f"  Summary    : {result.get('summary', '')}")
    print(f"  vs. prev   : {result.get('vs_previous', '')}")
    print(f"  Run saved  : {run_path}")
    print(bar)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*62}")
    print(f"  Compliance Memory Agent")
    print(f"  Model  : {MODEL}")
    print(f"  Run at : {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*62}\n")

    commit = get_commit_info()
    print(f"📌 {commit['hash']}  {commit['branch']}  —  {commit['message']}")
    print(f"   by {commit['author']}  on  {commit['date']}\n")

    rules  = load_rules()
    diff   = get_git_diff()
    runs   = load_all_runs()

    print(f"📚 Previous runs : {len(runs)}")
    print(f"📏 Diff size     : {len(diff):,} chars")
    print(f"📋 Rules loaded  : {rules.count('- id:')} rules\n")

    # Phase 1 — history
    print("⏳ Phase 1 — Summarising compliance history …")
    history_summary = phase1_summarise_history(runs)
    write_summary(history_summary)
    print("✅ History summarised\n")

    # Phase 2 — today's scan
    print("⏳ Phase 2 — Running compliance scan …")
    result = phase2_review(diff, rules, history_summary, commit)
    print("✅ Scan complete\n")

    # Persist
    run_data = {
        "date":            datetime.now(timezone.utc).isoformat(),
        "commit":          commit,
        "model_used":      MODEL,
        "findings":        result.get("findings", []),
        "summary":         result.get("summary", ""),
        "vs_previous":     result.get("vs_previous", ""),
        "trend":           result.get("trend", "STABLE"),
        "history_summary": history_summary,
    }
    run_path = save_run(run_data)

    print_report(commit, result, run_path)

    # Exit code
    high_count = len([f for f in result.get("findings", []) if f["severity"] == "HIGH"])
    if FAIL_ON_HIGH and high_count:
        print(f"\n❌ Blocking CI — {high_count} HIGH finding(s). "
              f"Set COMPLIANCE_FAIL_ON_HIGH=false to demote to warning.")
        sys.exit(1)
    elif high_count:
        print(f"\n⚠️  {high_count} HIGH finding(s) detected. "
              f"Set COMPLIANCE_FAIL_ON_HIGH=true to block CI merges.")
    else:
        print("\n✅ Compliance check passed — no HIGH findings.")


if __name__ == "__main__":
    main()
