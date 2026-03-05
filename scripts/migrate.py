#!/usr/bin/env python3
"""
Migration script: README.md → individual prompt files in prompts/<category>/

Usage:
  python scripts/migrate.py

Input:
  - README.md (source of all prompts)
  - scripts/manifest.json (category + metadata overrides)

Output:
  - prompts/<category>/<slug>.md for each prompt
  - scripts/migration-report.json (audit log)
"""

import re
import json
import unicodedata
from pathlib import Path
from datetime import date

# Paths
REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
MANIFEST = Path(__file__).parent / "manifest.json"
REPORT_OUT = Path(__file__).parent / "migration-report.json"
PROMPTS_DIR = REPO_ROOT / "prompts"
ADDED_DATE = date.today().isoformat()

# These headings in the Contents list are claudecode/ links — skip them
CLAUDECODE_HEADINGS = {
    "Claude Code Coding Prompt",
    "Claude Code Permission Mode Guide",
    "Claude Code Plan Mode Guide",
}


def make_slug(title: str) -> str:
    """Convert a title to a filesystem-safe hyphen-slug."""
    # Normalize unicode, strip accents
    title = unicodedata.normalize("NFKD", title)
    # Remove non-ASCII characters (emoji, CJK, etc.)
    title = title.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    title = title.lower()
    # Replace any non-alphanumeric char with hyphen
    title = re.sub(r"[^a-z0-9]+", "-", title)
    # Strip leading/trailing hyphens
    title = title.strip("-")
    # Truncate to 60 chars at a word boundary
    if len(title) > 60:
        title = title[:60].rsplit("-", 1)[0]
    return title


def write_frontmatter(f, title, meta):
    """Write YAML frontmatter block."""
    f.write("---\n")
    f.write(f'title: "{title}"\n')
    f.write(f'category: {meta["category"]}\n')
    tags = meta.get("tags", [])
    if tags:
        f.write("tags:\n")
        for tag in tags:
            f.write(f"  - {tag}\n")
    else:
        f.write("tags: []\n")
    source = meta.get("source") or "null"
    if source and source != "null":
        f.write(f'source: "{source}"\n')
    else:
        f.write("source: null\n")
    author = meta.get("author") or "null"
    if author and author != "null":
        f.write(f'author: "{author}"\n')
    else:
        f.write("author: null\n")
    model = meta.get("model") or "null"
    if model and model != "null":
        f.write(f'model: "{model}"\n')
    else:
        f.write("model: null\n")
    has_image = meta.get("has_image", False)
    f.write(f"has_image: {str(has_image).lower()}\n")
    dup = meta.get("duplicate_of")
    if dup:
        f.write(f'duplicate_of: "{dup}"\n')
    f.write(f"added: \"{ADDED_DATE}\"\n")
    f.write("---\n")


def rewrite_image_paths(text: str) -> str:
    """Rewrite imgs/ references to ../../imgs/ for two-level-deep files."""
    # Match ![alt](imgs/...) patterns
    text = re.sub(r'!\[([^\]]*)\]\(imgs/', r'![\1](../../imgs/', text)
    return text


def extract_attribution(lines):
    """Extract source URL from 'from: URL' or '> URL' blockquote patterns."""
    source = None
    filtered = []
    for line in lines:
        m = re.match(r'^>\s*from:\s*(https?://\S+)', line)
        if not m:
            m = re.match(r'^from:\s*(https?://\S+)', line)
        if not m:
            m = re.match(r'^>\s*(https?://\S+)\s*$', line)
        if m:
            source = m.group(1)
        else:
            filtered.append(line)
    return source, filtered


def parse_readme(readme_path):
    """
    Parse README.md and return a list of prompt dicts:
      {
        "title": str,
        "preamble": [str],   # lines before code block
        "codeblocks": [[str]],  # list of code block line lists
        "postamble": [str],  # lines after last code block
        "source_lines": (start, end),
        "warnings": [str]
      }
    """
    lines = readme_path.read_text(encoding="utf-8").splitlines()
    prompts = []

    # States
    SCAN = "SCAN"
    PREAMBLE = "PREAMBLE"
    IN_CODE = "IN_CODE"
    AFTER_CODE = "AFTER_CODE"

    state = SCAN
    current = None
    code_buf = []
    in_backtick_count = 0  # tracks ``` vs ```` fence depth

    # We only start collecting after the Contents section ends (line ~162)
    # Detect the first ## heading AFTER the Contents block
    contents_done = False

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()

        if state == SCAN:
            # Detect end of Contents block
            if not contents_done:
                # The first ## heading after "## Contents" that is not in Contents
                if stripped.startswith("## ") and not stripped.startswith("## Contents"):
                    # Check if this might be the first real prompt heading
                    # (Contents ends around line 162)
                    if i > 160:
                        contents_done = True

            if stripped.startswith("## ") and contents_done:
                title = stripped[3:].strip()
                if title in CLAUDECODE_HEADINGS:
                    continue
                # Start collecting this prompt
                current = {
                    "title": title,
                    "preamble": [],
                    "codeblocks": [],
                    "postamble": [],
                    "source_lines": (i, None),
                    "warnings": [],
                }
                state = PREAMBLE
                code_buf = []

        elif state == PREAMBLE:
            # Check for new ## heading (empty prompt, no code block)
            if stripped.startswith("## "):
                # Save current prompt without code block
                if current:
                    current["source_lines"] = (current["source_lines"][0], i - 1)
                    current["warnings"].append("no code block found")
                    prompts.append(current)
                # Start new
                title = stripped[3:].strip()
                if title in CLAUDECODE_HEADINGS:
                    current = None
                    state = SCAN
                else:
                    current = {
                        "title": title,
                        "preamble": [],
                        "codeblocks": [],
                        "postamble": [],
                        "source_lines": (i, None),
                        "warnings": [],
                    }
                    code_buf = []
                continue

            # Detect code fence opening
            fence_match = re.match(r'^(`{3,})', stripped)
            if fence_match:
                in_backtick_count = len(fence_match.group(1))
                state = IN_CODE
                code_buf = []
                continue

            current["preamble"].append(stripped)

        elif state == IN_CODE:
            # Detect matching closing fence
            close_match = re.match(r'^(`{' + str(in_backtick_count) + r'})\s*$', stripped)
            if close_match:
                current["codeblocks"].append(code_buf)
                code_buf = []
                state = AFTER_CODE
                continue
            code_buf.append(line.rstrip())

        elif state == AFTER_CODE:
            # Check for new ## heading
            if stripped.startswith("## "):
                # Finish current prompt
                if current:
                    current["source_lines"] = (current["source_lines"][0], i - 1)
                    if len(current["codeblocks"]) > 1:
                        current["warnings"].append(
                            f"multiple code blocks ({len(current['codeblocks'])}), all preserved"
                        )
                    prompts.append(current)
                # Start new
                title = stripped[3:].strip()
                if title in CLAUDECODE_HEADINGS:
                    current = None
                    state = SCAN
                    contents_done = True  # We're past contents for sure
                else:
                    current = {
                        "title": title,
                        "preamble": [],
                        "codeblocks": [],
                        "postamble": [],
                        "source_lines": (i, None),
                        "warnings": [],
                    }
                    code_buf = []
                    state = PREAMBLE
                continue

            # Check for another code fence (second code block)
            fence_match = re.match(r'^(`{3,})', stripped)
            if fence_match:
                in_backtick_count = len(fence_match.group(1))
                state = IN_CODE
                code_buf = []
                continue

            current["postamble"].append(stripped)

    # Don't forget the last prompt
    if current and state in (AFTER_CODE, PREAMBLE):
        current["source_lines"] = (current["source_lines"][0], len(lines))
        if state == PREAMBLE:
            current["warnings"].append("no code block found")
        if len(current.get("codeblocks", [])) > 1:
            current["warnings"].append(
                f"multiple code blocks ({len(current['codeblocks'])}), all preserved"
            )
        prompts.append(current)

    return prompts


def build_body(prompt_dict):
    """Build the markdown body (below frontmatter) for a prompt."""
    title = prompt_dict["title"]
    preamble = prompt_dict["preamble"]
    codeblocks = prompt_dict["codeblocks"]
    postamble = prompt_dict["postamble"]

    parts = []
    parts.append(f"# {title}")
    parts.append("")

    # Filter attribution lines from preamble; rewrite image paths
    _, preamble_clean = extract_attribution(preamble)
    preamble_text = "\n".join(preamble_clean).strip()
    preamble_text = rewrite_image_paths(preamble_text)
    if preamble_text:
        parts.append(preamble_text)
        parts.append("")

    if not codeblocks:
        parts.append("<!-- No prompt code block found in original README. See source for details. -->")
    else:
        for idx, block_lines in enumerate(codeblocks):
            if idx > 0:
                parts.append("")
                parts.append("<!-- additional code block -->")
            block_text = "\n".join(block_lines)
            block_text = rewrite_image_paths(block_text)
            parts.append("```")
            parts.append(block_text)
            parts.append("```")

    if postamble:
        postamble_text = "\n".join(postamble).strip()
        postamble_text = rewrite_image_paths(postamble_text)
        if postamble_text:
            parts.append("")
            parts.append(postamble_text)

    return "\n".join(parts) + "\n"


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prompts = parse_readme(README)

    report = []
    slug_counts = {}

    for p in prompts:
        title = p["title"]
        warnings = list(p["warnings"])

        # Look up manifest
        meta = manifest.get(title)
        if not meta:
            # Try case-insensitive match
            for k, v in manifest.items():
                if k.lower() == title.lower():
                    meta = v
                    break

        if not meta:
            warnings.append(f"title not found in manifest, defaulting to 'business'")
            meta = {"category": "business", "tags": []}

        # Extract source from preamble if not in manifest
        preamble_source, _ = extract_attribution(p["preamble"])
        if preamble_source and not meta.get("source"):
            meta = dict(meta)
            meta["source"] = preamble_source

        category = meta["category"]
        slug = make_slug(title)

        # Handle slug collisions
        if slug in slug_counts:
            slug_counts[slug] += 1
            slug = f"{slug}-{slug_counts[slug]}"
        else:
            slug_counts[slug] = 1

        out_path = PROMPTS_DIR / category / f"{slug}.md"

        # Write the file
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            write_frontmatter(f, title, meta)
            f.write("\n")
            f.write(build_body(p))

        report.append({
            "title": title,
            "slug": slug,
            "category": category,
            "output": str(out_path.relative_to(REPO_ROOT)),
            "source_lines": list(p["source_lines"]),
            "warnings": warnings,
        })

        status = "OK" if not warnings else f"WARN: {'; '.join(warnings)}"
        print(f"  [{status}] {out_path.relative_to(REPO_ROOT)}")

    REPORT_OUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nMigrated {len(prompts)} prompts.")
    print(f"Report written to {REPORT_OUT.relative_to(REPO_ROOT)}")

    warn_count = sum(1 for r in report if r["warnings"])
    if warn_count:
        print(f"  {warn_count} prompts had warnings — review migration-report.json")


if __name__ == "__main__":
    main()
