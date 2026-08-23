#!/usr/bin/env python3
"""
Security Vulnerability Agent
=============================
Stateful security scanner for Spring Boot + Oracle DB repos.
Triggered from VSCode Copilot Agent chat or terminal.

  • Maintains a persistent vulnerability registry (V-001, V-002 …)
  • Phase 1 — loads all past findings, summarises open attack surface
  • Phase 2 — scans today's git diff, links NEW findings to PAST ones
  • The linking is the demo moment: "same root cause as V-003 from last week"

Set up: copy .env.example → .env, fill in your API key, then run:
    python security_agent.py
"""

import os
import json
import sys
import subprocess
import yaml
from datetime import datetime, timezone
from pathlib import Path

# ── Load .env automatically ────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

import litellm
litellm.suppress_debug_info = True

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT      = Path(__file__).parent
MEMORY_DIR     = REPO_ROOT / ".security-memory"
RUNS_DIR       = MEMORY_DIR / "runs"
REGISTRY_FILE  = MEMORY_DIR / "registry.json"   # persistent vulnerability IDs
SUMMARY_FILE   = MEMORY_DIR / "summary.md"
RULES_FILE     = MEMORY_DIR / "security-rules.yaml"

# ── Model config ───────────────────────────────────────────────────────────────
MODEL      = os.getenv("LLM_MODEL", "claude-opus-4-5")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
FAIL_ON_CRITICAL = os.getenv("SECURITY_FAIL_ON_CRITICAL", "false").lower() == "true"


# ── Startup validation ─────────────────────────────────────────────────────────

def validate_environment():
    provider_keys = {
        "claude":  "ANTHROPIC_API_KEY",
        "gpt":     "OPENAI_API_KEY",
        "openai":  "OPENAI_API_KEY",
        "azure":   "AZURE_API_KEY",
        "gemini":  "GEMINI_API_KEY",
    }
    for prefix, key in provider_keys.items():
        if MODEL.startswith(prefix) or f"/{prefix}" in MODEL:
            if not os.getenv(key):
                print(f"\n❌  Missing API key for model '{MODEL}'")
                print(f"    Set {key} in your .env file.")
                print(f"    Copy .env.example → .env and fill in your key.\n")
                sys.exit(1)
            break
    if MODEL.startswith("azure") and not os.getenv("AZURE_API_BASE"):
        print("\n❌  Azure model requires AZURE_API_BASE in .env\n")
        sys.exit(1)


# ── LLM helper ─────────────────────────────────────────────────────────────────

def llm_call(system: str, user: str) -> str:
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
        print(f"    Model: {MODEL} — check your API key in .env\n")
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
    count = get_commit_count()
    if count >= 2:
        diff = run_git("diff", "HEAD~1", "HEAD", "--unified=5",
                       "--diff-filter=ACM", "--", "*.java", "pom.xml",
                       "build.gradle", "build.gradle.kts", "*.xml", "*.properties",
                       "*.yml", "*.yaml")
    else:
        diff = run_git("show", "--unified=5", "HEAD")
    return diff or "(no changes detected — commit something first)"


def get_commit_info() -> dict:
    return {
        "hash":    run_git("rev-parse", "--short", "HEAD") or "unknown",
        "branch":  run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
        "message": run_git("log", "-1", "--pretty=%s") or "no commit message",
        "author":  run_git("log", "-1", "--pretty=%an") or "unknown",
        "date":    run_git("log", "-1", "--pretty=%ci") or "",
    }


# ── Registry helpers ───────────────────────────────────────────────────────────
#
# registry.json is the persistent source of truth for all vulnerability IDs.
# Every finding ever discovered gets a stable V-NNN ID that survives across runs.
# This is what enables cross-run linking: "new finding matches V-003's pattern."

def load_registry() -> list:
    if not REGISTRY_FILE.exists():
        return []
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_registry(registry: list):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def next_vuln_id(registry: list) -> str:
    if not registry:
        return "V-001"
    existing = [int(e["id"].split("-")[1]) for e in registry if e.get("id","").startswith("V-")]
    return f"V-{max(existing) + 1:03d}" if existing else "V-001"


def upsert_registry(registry: list, findings: list, run_id: str) -> list:
    """
    Merge today's findings into the persistent registry.
    - If a finding matches an existing entry (same rule + same file), update it.
    - If it's brand new, assign the next V-NNN ID.
    Returns the updated registry.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for f in findings:
        matched = next(
            (e for e in registry
             if e["rule"] == f.get("rule") and e["file"] == f.get("file")),
            None
        )
        if matched:
            matched["last_seen"]   = today
            matched["occurrences"] = matched.get("occurrences", 1) + 1
            matched["status"]      = "OPEN" if not f.get("resolved") else "RESOLVED"
            if run_id not in matched.get("run_ids", []):
                matched.setdefault("run_ids", []).append(run_id)
        else:
            vid = next_vuln_id(registry)
            registry.append({
                "id":          vid,
                "rule":        f.get("rule", "UNKNOWN"),
                "severity":    f.get("severity", "MEDIUM"),
                "file":        f.get("file", "unknown"),
                "line":        f.get("line"),
                "first_seen":  today,
                "last_seen":   today,
                "occurrences": 1,
                "status":      "RESOLVED" if f.get("resolved") else "OPEN",
                "description": f.get("description", ""),
                "run_ids":     [run_id],
            })
            f["vuln_id"] = vid   # tag the finding with its new ID

    return registry


# ── Memory helpers ─────────────────────────────────────────────────────────────

def load_rules() -> str:
    if not RULES_FILE.exists():
        print(f"\n❌  Rules file not found: {RULES_FILE}")
        print(f"    Place security-rules.yaml in .security-memory/\n")
        sys.exit(1)
    with open(RULES_FILE) as f:
        return yaml.dump(yaml.safe_load(f), default_flow_style=False)


def load_all_runs() -> list:
    if not RUNS_DIR.exists():
        return []
    runs = []
    for f in sorted(RUNS_DIR.glob("*.json")):
        try:
            with open(f) as fp:
                runs.append(json.load(fp))
        except (json.JSONDecodeError, OSError):
            pass
    return runs


def save_run(data: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    data["run_id"] = run_id
    path = RUNS_DIR / f"{run_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path, run_id


def write_summary(text: str):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_FILE, "w") as f:
        f.write("# Security Vulnerability Summary\n")
        f.write(f"_Updated: {datetime.now(timezone.utc).isoformat()}_\n\n")
        f.write(text)


# ── JSON extraction ────────────────────────────────────────────────────────────

def extract_json(raw: str) -> dict:
    raw = raw.strip()
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"\n⚠️   JSON parse error ({e}) — saving empty result.")
        return {"findings": [], "summary": "Parse error — re-run.",
                "attack_surface": "", "vs_previous": "", "trend": "STABLE"}


# ── Phase 1 — Summarise history + open attack surface ─────────────────────────

def phase1_summarise(runs: list, registry: list) -> str:
    if not runs and not registry:
        return "No previous scans. This is the first security scan for this repository."

    open_vulns   = [e for e in registry if e.get("status") == "OPEN"]
    resolved     = [e for e in registry if e.get("status") == "RESOLVED"]
    recent_runs  = runs[-10:]

    system = """You are a senior application security engineer.
You receive a vulnerability registry (all known issues with IDs) and recent scan history.

Return a structured Markdown summary (under 500 words) covering:
1. Open vulnerability count by severity, with their V-IDs
2. Attack surface: which areas of the codebase are most at risk
3. Recurring patterns — same rule appearing in multiple files
4. What was resolved and when
5. Overall security posture: CRITICAL / AT-RISK / ACCEPTABLE / CLEAN

Be factual. Reference V-IDs specifically (V-001, V-003). No filler."""

    user = (
        f"## Vulnerability Registry\n"
        f"Open: {len(open_vulns)}  |  Resolved: {len(resolved)}\n\n"
        f"```json\n{json.dumps(open_vulns, indent=2)}\n```\n\n"
        f"## Recent Scans ({len(recent_runs)} shown)\n"
        f"```json\n{json.dumps(recent_runs, indent=2)}\n```"
    )
    return llm_call(system, user)


# ── Phase 2 — Scan today's diff, link to registry ─────────────────────────────

def phase2_scan(diff: str, rules: str, history_summary: str,
                registry: list, commit: dict) -> dict:

    open_vulns = [e for e in registry if e.get("status") == "OPEN"]
    registry_text = json.dumps(open_vulns, indent=2) if open_vulns else "[]"

    system = f"""You are a senior application security engineer performing a security code review.

SECURITY RULES:
{rules}

EXISTING OPEN VULNERABILITIES (with their V-IDs):
{registry_text}

SECURITY POSTURE CONTEXT:
{history_summary}

Review the git diff below. Return ONLY valid JSON — no fences, no prose:
{{
  "findings": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "rule": "RULE_ID",
      "file": "path/to/File.java",
      "line": 42,
      "description": "precise description of the vulnerability",
      "recommendation": "exact fix with code example if possible",
      "related_to": ["V-001", "V-003"],
      "new_pattern": true,
      "resolved": false
    }}
  ],
  "attack_surface": "one paragraph describing what attack paths exist in total",
  "summary": "one-paragraph summary of this scan",
  "vs_previous": "what is new vs last scan — NEW findings, RESOLVED findings, or UNCHANGED",
  "trend": "IMPROVING|STABLE|DEGRADING|CRITICAL"
}}

IMPORTANT for related_to:
- If a finding matches the SAME ROOT CAUSE as an existing V-ID (same rule, same pattern,
  even in a different file), list those V-IDs in related_to.
- This is the key feature — show that the team has a systemic issue, not isolated bugs.
- If no relation exists, use an empty array.

Return only valid JSON."""

    diff_excerpt = diff[:12000]
    if len(diff) > 12000:
        diff_excerpt += f"\n\n... ({len(diff) - 12000} chars omitted)"

    user = (
        f"Commit : {commit['hash']} on '{commit['branch']}'\n"
        f"Author : {commit['author']}\n"
        f"Date   : {commit['date']}\n"
        f"Message: {commit['message']}\n\n"
        f"Git diff:\n{diff_excerpt}"
    )

    return extract_json(llm_call(system, user))


# ── Console report ─────────────────────────────────────────────────────────────

SEV_ICON  = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

def print_report(commit: dict, result: dict, registry: list, run_path: Path):
    findings  = result.get("findings", [])
    critical  = [f for f in findings if f.get("severity") == "CRITICAL"]
    high      = [f for f in findings if f.get("severity") == "HIGH"]
    medium    = [f for f in findings if f.get("severity") == "MEDIUM"]
    low       = [f for f in findings if f.get("severity") == "LOW"]
    open_total = len([e for e in registry if e.get("status") == "OPEN"])

    bar = "─" * 66
    print(f"\n{bar}")
    print(f"  SECURITY VULNERABILITY REPORT  ·  {commit['hash']}  ·  {commit['branch']}")
    print(bar)
    print(f"  Model        : {MODEL}")
    print(f"  🚨 CRITICAL  : {len(critical)}")
    print(f"  🔴 HIGH      : {len(high)}")
    print(f"  🟡 MEDIUM    : {len(medium)}")
    print(f"  🟢 LOW       : {len(low)}")
    print(f"  Open (total) : {open_total}  (all runs combined)")
    print(f"  Trend        : {result.get('trend', 'N/A')}")
    print()

    sorted_f = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity","LOW"), 4))

    if sorted_f:
        for f in sorted_f:
            icon = SEV_ICON.get(f.get("severity","LOW"), "⚪")
            vid  = f.get("vuln_id", "")
            vid_label = f"  [{vid}]" if vid else ""
            related = f.get("related_to", [])

            print(f"  {icon} [{f.get('severity','?')}]{vid_label}  {f.get('rule','?')}")
            print(f"     File   : {f.get('file','?')}  line {f.get('line','?')}")
            print(f"     Issue  : {f.get('description','')}")
            print(f"     Fix    : {f.get('recommendation','')}")
            if related:
                print(f"     ⚠️  Related to : {', '.join(related)} — same pattern, systemic issue")
            print()
    else:
        print("  ✅ No new vulnerabilities found in this commit.\n")

    if result.get("attack_surface"):
        print(f"  Attack surface: {result['attack_surface']}")
        print()

    print(f"  Summary   : {result.get('summary','')}")
    print(f"  vs. prev  : {result.get('vs_previous','')}")
    print(f"  Saved to  : {run_path}")
    print(bar)

    # Registry snapshot
    open_vulns = [e for e in registry if e.get("status") == "OPEN"]
    if open_vulns:
        print(f"\n  📋 OPEN VULNERABILITY REGISTRY  ({len(open_vulns)} total)")
        print(f"  {'ID':<8} {'Severity':<10} {'Rule':<30} {'File':<35} {'Seen'}")
        print(f"  {'─'*7} {'─'*9} {'─'*29} {'─'*34} {'─'*10}")
        for e in sorted(open_vulns, key=lambda x: SEV_ORDER.get(x.get("severity","LOW"), 4)):
            icon = SEV_ICON.get(e.get("severity","LOW"), "⚪")
            fname = Path(e.get("file","?")).name
            print(f"  {e['id']:<8} {icon} {e.get('severity','?'):<8} "
                  f"{e.get('rule','?'):<30} {fname:<35} {e.get('first_seen','?')}")
        print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    validate_environment()

    print(f"\n{'='*66}")
    print(f"  Security Vulnerability Agent  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Model: {MODEL}")
    print(f"{'='*66}\n")

    commit = get_commit_info()
    print(f"📌 {commit['hash']}  [{commit['branch']}]  —  {commit['message']}")
    print(f"   by {commit['author']}  ·  {commit['date']}\n")

    rules    = load_rules()
    diff     = get_git_diff()
    runs     = load_all_runs()
    registry = load_registry()

    rule_count = rules.count("- id:")
    open_count = len([e for e in registry if e.get("status") == "OPEN"])
    print(f"📚 Previous runs    : {len(runs)}")
    print(f"🗂️  Registry entries : {len(registry)}  ({open_count} open)")
    print(f"📋 Rules loaded     : {rule_count}")
    print(f"📏 Diff size        : {len(diff):,} chars\n")

    # Phase 1
    print("⏳ Phase 1 — Analysing attack surface from all past findings …")
    history_summary = phase1_summarise(runs, registry)
    write_summary(history_summary)
    print("✅ Attack surface analysed\n")

    # Phase 2
    print("⏳ Phase 2 — Scanning today's diff for vulnerabilities …")
    result = phase2_scan(diff, rules, history_summary, registry, commit)
    print("✅ Scan complete\n")

    # Generate temp run_id for registry upsert
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")

    # Update registry with today's findings
    findings = result.get("findings", [])
    registry = upsert_registry(registry, findings, run_id)
    save_registry(registry)

    # Save run
    run_data = {
        "date":            datetime.now(timezone.utc).isoformat(),
        "commit":          commit,
        "model_used":      MODEL,
        "findings":        findings,
        "attack_surface":  result.get("attack_surface", ""),
        "summary":         result.get("summary", ""),
        "vs_previous":     result.get("vs_previous", ""),
        "trend":           result.get("trend", "STABLE"),
        "history_summary": history_summary,
        "run_id":          run_id,
    }
    run_path = RUNS_DIR / f"{run_id}.json"
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(run_path, "w") as f:
        json.dump(run_data, f, indent=2)

    print_report(commit, result, registry, run_path)

    # Exit code
    critical_count = len([f for f in findings if f.get("severity") == "CRITICAL"])
    if FAIL_ON_CRITICAL and critical_count:
        print(f"\n❌ Blocking — {critical_count} CRITICAL finding(s). "
              "Set SECURITY_FAIL_ON_CRITICAL=false in .env to demote to warning.")
        sys.exit(1)
    elif critical_count:
        print(f"\n🚨 {critical_count} CRITICAL vulnerability(ies) found. "
              "Set SECURITY_FAIL_ON_CRITICAL=true in .env to block CI.")
    else:
        print("\n✅ Security scan passed — no CRITICAL vulnerabilities in this commit.")


if __name__ == "__main__":
    main()
