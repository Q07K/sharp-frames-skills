"""Read-only marker candidate inventory; not a semantic debt detector."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tokenize

DEFAULT_MARKERS = ('TODO', 'FIXME', 'HACK', 'XXX', 'shortcut', 'tech-debt', 'ponytail')
SOURCE_SUFFIXES = {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java', '.c', '.h', '.cpp', '.cs', '.rb', '.sh', '.ps1', '.sql', '.yaml', '.yml', '.toml', '.html', '.vue', '.svelte', '.css', '.scss', '.kt', '.swift', '.php', '.lua'}
EXCLUDED_PARTS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', '.next'}


def inventory(root: Path, markers=DEFAULT_MARKERS, max_bytes=1_000_000):
    root = root.resolve()
    listed = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True)
    if listed.returncode:
        raise ValueError('Git file inventory unavailable; use a Git checkout or inspect candidates manually. No clean-scan claim is possible.')
    expression = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(m) for m in markers) + r')(?![\w-])\s*:?\s*(.*)', re.IGNORECASE)
    hits, skipped = [], []
    files = sorted(set(listed.stdout.decode('utf-8', errors='surrogateescape').rstrip('\0').split('\0')) - {''})
    scanned = 0
    for relative in files:
        path = root / relative
        parts = Path(relative).parts
        reason = None
        if any(p in EXCLUDED_PARTS for p in parts):
            reason = 'generated/vendor/cache path'
        elif path.is_symlink() or not path.resolve().is_relative_to(root):
            reason = 'symlink or external path'
        elif path.suffix.lower() not in SOURCE_SUFFIXES and path.name not in ('Dockerfile', 'Makefile'):
            reason = 'unsupported source type'
        elif not path.is_file():
            reason = 'missing or non-file path'
        if reason:
            skipped.append({'path': relative, 'reason': reason})
            continue
        try:
            if path.stat().st_size > max_bytes:
                skipped.append({'path': relative, 'reason': 'size limit'})
                continue
            content = path.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as error:
            skipped.append({'path': relative, 'reason': type(error).__name__})
            continue
        comments = []
        if path.suffix.lower() == '.py':
            try:
                for token in tokenize.generate_tokens(io.StringIO(content).readline):
                    if token.type == tokenize.COMMENT:
                        comments.append((token.start[0], token.string[1:], 'python-comment'))
            except (tokenize.TokenError, IndentationError, SyntaxError) as error:
                skipped.append({'path': relative, 'reason': f'partial tokenization: {type(error).__name__}'})
        else:
            # This can include comment-like strings and misses some language forms.
            # Results stay candidates; no claim of full language parsing is made.
            for number, line in enumerate(content.splitlines(), 1):
                comment = re.search(r'//|/\*|<!--|--|^\s*[#*]', line)
                if comment:
                    comments.append((number, line[comment.end():], 'comment-heuristic'))
        for number, comment, kind in comments:
            match = expression.search(comment)
            if match:
                hits.append({'path': relative, 'line': number, 'marker': match.group(1), 'text': match.group(2).strip(), 'evidence_kind': kind, 'needs_context_review': True})
        scanned += 1
    return {'schema_version': 1, 'scope': str(root), 'source': 'git tracked + untracked nonignored files', 'files_considered': len(files), 'files_scanned': scanned, 'candidates': hits, 'skipped': skipped, 'semantic_debt_assessment': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--marker', action='append', help='Replace defaults with one or more literal marker words')
    parser.add_argument('--max-bytes', type=int, default=1_000_000)
    args = parser.parse_args()
    if args.max_bytes <= 0 or (args.marker and any(not m.strip() for m in args.marker)):
        parser.error('max-bytes must be positive and marker words must be nonempty')
    try:
        result = inventory(args.root, args.marker or DEFAULT_MARKERS, args.max_bytes)
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
