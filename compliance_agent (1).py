#!/usr/bin/env python3
"""
Compliance Memory Agent
=======================
Stateful compliance reviewer for Spring Boot + Oracle DB repos.
Triggered from VSCode Copilot Agent chat or terminal.

  • Remembers every past scan in .compliance-memory/runs/
  • Phase 1 — summarises all history via LLM
  • Phase 2 — reviews today's git diff against compliance rules
  • Model-agnostic via LiteLLM (Claude / GPT-4o / Azure Copilot / Codex)

Set up: copy .env.example → .env, fill in your API key, then run:
    python compliance_agent.py
"""

import os
import json
import sys
import subprocess
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

# ── Load .env automatically (no need to export manually) ──────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)   # won't overwrite keys already in environment
except ImportError:
    pass  # dotenv optional; keys can be set manually in the shell

import litellm
litellm.suppress_debug_info = True

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).parent
MEMORY_DIR   = REPO_ROOT / ".compliance-memory"
RUNS_DIR     = MEMORY_DIR / "runs"
SUMMARY_FILE = MEMORY_DIR / "summary.md"
RULES_FILE   = MEMORY_DIR / "compliance-rules.yaml"

# ── Model config ───────────────────────────────────────────────────────────────
# Change LLM_MODEL in your .env to switch providers — no code edits needed.
#
#   claude-opus-4-5          → Anthropic Claude   (ANTHROPIC_API_KEY)
#   claude-sonnet-4-5        → Claude Sonnet      (ANTHROPIC_API_KEY)
#   gpt-4o                   → OpenAI             (OPENAI_API_KEY)
#   azure/gpt-4o             → Azure / Copilot    (AZURE_API_KEY + AZURE_API_BASE)
#   openai/gpt-3.5-turbo     → Codex              (OPENAI_API_KEY)
MODEL      = os.getenv("LLM_MODEL", "claude-opus-4-5")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
FAIL_ON_HIGH = os.getenv("COMPLIANCE_FAIL_ON_HIGH", "false").lower() == "true"


# ── Startup validation ─────────────────────────────────────────────────────────

def validate_environment():
    """Fail fast with a clear message if required config is missing."""
    provider_keys = {
        "claude":  "ANTHROPIC_API_KEY",
        "gpt":     "OPENAI_API_KEY",
        "openai":  "OPENAI_API_KEY",
        "azure":   "AZURE_API_KEY",
        "gemini":  "GEMINI_API_KEY",
        "bedrock": "AWS_ACCESS_KEY_ID",
    }
    required_key = None
    for prefix, key in provider_keys.items():
        if MODEL.startswith(prefix) or f"/{prefix}" in MODEL:
            required_key = key
            break
    if required_key and not os.getenv(required_key):
        print(f"\n❌  Missing API key for model '{MODEL}'")
        print(f"    Set {required_key} in your .env file or shell environment.")
        print(f"    Copy .env.example → .env and fill in your key.\n")
        sys.exit(1)

    if MODEL.startswith("azure") and not os.getenv("AZURE_API_BASE"):
        print("\n❌  Azure model requires AZURE_API_BASE in .env\n")
        sys.exit(1)


# ── LLM helper ────────────────────────────────────────────────────────────────

def llm_call(system: str, user: str) -> str:
    """Single LLM call. Model-agnostic via LiteLLM."""
    try:
        response = litellm.completion(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"\n❌  LLM call failed: {e}")
        print(f"    Model: {MODEL}")
        print(f"    Check your API key and model name in .env\n")
        sys.exit(1)


# ── Git helpers ────────────────────────────────────────────────────────────────

def run_git(*args) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True,
                            cwd=str(REPO_ROOT))
    return result.stdout.strip()


def get_commit_count() -> int:
    out = run_git("rev-list", "--count", "HEAD")
    return int(out) if out.isdigit() else 0


def get_git_diff() -> str:
    """
    Returns the Java file diff for the last commit.
    Handles repos with only a single commit gracefully.
    """
    count = get_commit_count()
    if count >= 2:
        diff = run_git("diff", "HEAD~1", "HEAD",
                       "--unified=5", "--diff-filter=ACM", "--", "*.java")
    else:
        # First-ever commit — show all Java files as new
        diff = run_git("show", "--unified=5", "HEAD", "--", "*.java")

    if not diff:
        diff = run_git("diff", "HEAD~1", "HEAD", "--unified=5")  # all files fallback
    return diff or "(no changes detected — commit something first)"


def get_commit_info() -> dict:
    return {
        "hash":    run_git("rev-parse", "--short", "HEAD") or "unknown",
        "branch":  run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "message": run_git("log", "-1", "--pretty=%s") or "no commit message",
        "author":  run_git("log", "-1", "--pretty=%an") or "unknown",
        "date":    run_git("log", "-1", "--pretty=%ci") or "",
    }


# ── Memory helpers ─────────────────────────────────────────────────────────────

def load_rules() -> str:
    if not RULES_FILE.exists():
        print(f"⚠️   Rules file not found at {RULES_FILE}")
        print(f"    Place compliance-rules.yaml in .compliance-memory/")
        sys.exit(1)
    with open(RULES_FILE) as f:
        data = yaml.safe_load(f)
    return yaml.dump(data, default_flow_style=False)


def load_all_runs() -> list:
    if not RUNS_DIR.exists():
        return []
    runs = []
    for f in sorted(RUNS_DIR.glob("*.json")):
        try:
            with open(f) as fp:
                runs.append(json.load(fp))
        except (json.JSONDecodeError, OSError):
            print(f"⚠️   Skipping corrupt run file: {f.name}")
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
        f.write("# Compliance History Summary\n")
        f.write(f"_Updated: {datetime.now(timezone.utc).isoformat()}_\n\n")
        f.write(text)


# ── JSON extraction (handles models that wrap output in fences) ────────────────

def extract_json(raw: str) -> dict:
    """
    Robustly parse JSON from LLM output.
    Handles: plain JSON, ```json fences, leading/trailing prose.
    """
    # Strip markdown fences
    raw = raw.strip()
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    # Find the outermost JSON object
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"\n⚠️   JSON parse failed ({e}). Raw LLM output:\n{raw[:500]}\n")
        # Return a safe fallback so the run still saves
        return {
            "findings": [],
            "summary": "LLM returned malformed JSON — re-run to retry.",
            "vs_previous": "Parse error — unable to compare.",
            "trend": "STABLE",
        }


# ── Phase 1 — Summarise history ────────────────────────────────────────────────

def phase1_summarise_history(runs: list) -> str:
    if not runs:
        return "No previous runs. This is the first compliance scan for this repository."

    recent    = runs[-20:]   # last 20 runs to stay within context
    runs_json = json.dumps(recent, indent=2)

    system = """You are a compliance trend analyst for Java Spring Boot codebases.
You receive JSON from past compliance scans.

Return a structured Markdown summary (under 400 words) covering:
1. Total runs and date range
2. Recurring unresolved findings — rule ID, file, count
3. Findings that were fixed between runs
4. Overall trend: IMPROVING / STABLE / DEGRADING with a short reason
5. Top 3 risk areas right now

Be factual and concise. No filler."""

    user = f"Past compliance scans ({len(recent)} most recent of {len(runs)} total):\n\n```json\n{runs_json}\n```"
    return llm_call(system, user)


# ── Phase 2 — Today's compliance review ───────────────────────────────────────

def phase2_review(diff: str, rules: str, history_summary: str, commit: dict) -> dict:
    system = f"""You are a senior security and compliance engineer reviewing a Java Spring Boot + Oracle DB repo.

COMPLIANCE RULES:
{rules}

HISTORY CONTEXT (from all previous scans):
{history_summary}

Review the git diff. Return ONLY a valid JSON object — no markdown fences, no extra prose:
{{
  "findings": [
    {{
      "severity": "HIGH|MEDIUM|LOW",
      "rule": "RULE_ID",
      "file": "path/to/File.java",
      "line": 42,
      "description": "specific violation description",
      "recommendation": "exact fix",
      "resolved": false
    }}
  ],
  "summary": "one-paragraph plain English summary of this scan",
  "vs_previous": "what changed vs the last scan — new findings, resolved findings, or no change",
  "trend": "IMPROVING|STABLE|DEGRADING"
}}

Return only valid JSON. If no findings, return an empty findings array."""

    diff_excerpt = diff[:12000]
    if len(diff) > 12000:
        diff_excerpt += f"\n\n... (diff truncated — {len(diff) - 12000} chars omitted. Review remaining diff manually.)"

    user = (
        f"Commit : {commit['hash']} on '{commit['branch']}'\n"
        f"Author : {commit['author']}\n"
        f"Date   : {commit['date']}\n"
        f"Message: {commit['message']}\n\n"
        f"Git diff:\n{diff_excerpt}"
    )

    raw = llm_call(system, user)
    return extract_json(raw)


# ── Console report ─────────────────────────────────────────────────────────────

SEVERITY_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

def print_report(commit: dict, result: dict, run_path: Path):
    findings = result.get("findings", [])
    high   = [f for f in findings if f.get("severity") == "HIGH"]
    medium = [f for f in findings if f.get("severity") == "MEDIUM"]
    low    = [f for f in findings if f.get("severity") == "LOW"]

    bar = "─" * 64
    print(f"\n{bar}")
    print(f"  COMPLIANCE REPORT  ·  {commit['hash']}  ·  {commit['branch']}")
    print(bar)
    print(f"  Model    : {MODEL}")
    print(f"  🔴 HIGH  : {len(high)}")
    print(f"  🟡 MEDIUM: {len(medium)}")
    print(f"  🟢 LOW   : {len(low)}")
    print(f"  Trend    : {result.get('trend', 'N/A')}")
    print()

    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(f.get("severity", "LOW"), 3)
    )

    if sorted_findings:
        for f in sorted_findings:
            icon = SEVERITY_ICON.get(f.get("severity", "LOW"), "⚪")
            print(f"  {icon} [{f.get('severity','?')}] {f.get('rule','?')}")
            print(f"     File : {f.get('file','?')}  line {f.get('line','?')}")
            print(f"     Issue: {f.get('description','')}")
            print(f"     Fix  : {f.get('recommendation','')}")
            print()
    else:
        print("  ✅ No findings in this commit.\n")

    print(f"  Summary   : {result.get('summary', '')}")
    print(f"  vs. prev  : {result.get('vs_previous', '')}")
    print(f"  Saved to  : {run_path}")
    print(bar)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    validate_environment()

    print(f"\n{'='*64}")
    print(f"  Compliance Memory Agent  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Model: {MODEL}")
    print(f"{'='*64}\n")

    commit = get_commit_info()
    print(f"📌 {commit['hash']}  [{commit['branch']}]  —  {commit['message']}")
    print(f"   by {commit['author']}  ·  {commit['date']}\n")

    rules = load_rules()
    diff  = get_git_diff()
    runs  = load_all_runs()

    rule_count = rules.count("- id:")
    print(f"📚 Previous runs  : {len(runs)}")
    print(f"📋 Rules loaded   : {rule_count}")
    print(f"📏 Diff size      : {len(diff):,} chars\n")

    # Phase 1
    print("⏳ Phase 1 — Summarising compliance history …")
    history_summary = phase1_summarise_history(runs)
    write_summary(history_summary)
    print("✅ History summarised\n")

    # Phase 2
    print("⏳ Phase 2 — Running compliance scan on today's diff …")
    result = phase2_review(diff, rules, history_summary, commit)
    print("✅ Scan complete\n")

    # Save
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
    high_count = len([f for f in result.get("findings", []) if f.get("severity") == "HIGH"])
    if FAIL_ON_HIGH and high_count:
        print(f"\n❌ Blocking — {high_count} HIGH finding(s). "
              "Set COMPLIANCE_FAIL_ON_HIGH=false in .env to demote to warning.")
        sys.exit(1)
    elif high_count:
        print(f"\n⚠️  {high_count} HIGH finding(s). "
              "Set COMPLIANCE_FAIL_ON_HIGH=true in .env to block CI.")
    else:
        print("\n✅ Compliance check passed.")


if __name__ == "__main__":
    main()
