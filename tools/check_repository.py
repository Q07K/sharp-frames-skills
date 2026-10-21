"""Validate distributable skill structure and run the unchanged sample fixture."""

from pathlib import Path
import json
import re
import subprocess
import sys

import yaml

from render_catalog import END, START, table


ROOT = Path(__file__).resolve().parents[1]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    skills = list((ROOT / "skills").glob("*/SKILL.md"))
    check(bool(skills), "No skills found")
    for path in skills:
        content = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.DOTALL)
        check(match is not None, f"Invalid frontmatter: {path}")
        meta = yaml.safe_load(match.group(1))
        check(isinstance(meta, dict), "Frontmatter must be a mapping")
        name = meta.get("name", "")
        description = meta.get("description", "")
        check(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)), "Invalid skill name")
        check(len(name) < 65 and name == path.parent.name, "Name/folder mismatch")
        check(isinstance(description, str) and 0 < len(description) <= 1024, "Invalid description")
        check("[TODO:" not in content, "Unfinished initializer placeholder")
        ui = yaml.safe_load((path.parent / "agents/openai.yaml").read_text(encoding="utf-8"))
        check(isinstance(ui, dict), "UI metadata must be a mapping")
        interface = ui.get("interface", {})
        check(isinstance(interface.get("display_name"), str), "Missing skill display name")
        short = interface.get("short_description", "")
        check(isinstance(short, str) and 25 <= len(short) <= 64, "Invalid short UI description")
        policy = ui.get("policy", {})
        check(policy.get("allow_implicit_invocation", True) is True, "Automatic discovery unexpectedly disabled")

    catalog = json.loads((ROOT / "skills/sharp-frames-help/references/catalog.json").read_text(encoding="utf-8"))
    commands = catalog["commands"]
    names = [c["name"] for c in commands]
    check(len(names) == len(set(names)), "Duplicate command catalog entry")
    check(set(names) == {p.parent.name for p in skills}, "Skill catalog does not match distributed folders")
    for command in commands:
        check(isinstance(command["edits_source"], bool), "Command edit behavior must be explicit")
        check(command["purpose_ko"] and "$" + command["name"] in command["example"], "Incomplete command example")
    for document in (ROOT / "README.md", ROOT / "docs/commands.md"):
        content = document.read_text(encoding="utf-8")
        check(content.count(START) == 1 and content.count(END) == 1, "Missing catalog marker pair")
        rendered = content.split(START)[1].split(END)[0].strip()
        check(rendered == table(), f"Stale command table: {document}; run tools/render_catalog.py --write")

    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            check((path.parent / target).exists(), f"Broken local link in {path}: {target}")

    cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))
    check(cases["skill_name"] in [p.parent.name for p in skills], "Unknown evaluation skill")
    ids = [c["id"] for c in cases["evals"]]
    check(len(ids) == len(set(ids)), "Duplicate evaluation IDs")
    for case in cases["evals"]:
        check(bool(case["prompt"] and case["expected_output"] and case["assertions"]), "Incomplete evaluation")
        for fixture in case["files"]:
            check((ROOT / fixture).is_dir(), f"Missing fixture: {fixture}")
    triggers = json.loads((ROOT / "evals/triggers.json").read_text(encoding="utf-8"))
    check(any(c["should_trigger"] for c in triggers), "No positive routing cases")
    check(any(not c["should_trigger"] for c in triggers), "No negative routing cases")
    check(all(isinstance(c["should_trigger"], bool) and c["query"] for c in triggers), "Invalid routing case")
    trigger_ids = [c["id"] for c in triggers]
    check(all(trigger_ids) and len(trigger_ids) == len(set(trigger_ids)), "Invalid routing case IDs")
    check(all(c["skill"] in names for c in triggers), "Unknown routing target skill")

    fixture = ROOT / "evals/fixtures/shop"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=fixture,
        text=True,
        capture_output=True,
    )
    check(result.returncode == 0, "Baseline fixture failed:\n" + result.stdout + result.stderr)
    print(f"Validated {len(skills)} skill(s), {len(ids)} behavioral prompts, {len(triggers)} routing cases, and baseline fixture.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
