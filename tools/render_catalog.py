"""Render the public command table from the help skill's canonical catalog."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'skills/sharp-frames-help/references/catalog.json'
START = '<!-- sharp-frames-catalog:start -->'
END = '<!-- sharp-frames-catalog:end -->'


def table():
    commands = json.loads(CATALOG.read_text(encoding='utf-8'))['commands']
    lines = ['| 호출 | 역할 | 소스 수정 |', '| --- | --- | --- |']
    for command in commands:
        lines.append(f"| `${command['name']}` | {command['purpose_ko']} | {'요청 범위 내 수정' if command['edits_source'] else '읽기·보고'} |")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Update existing marked docs')
    args = parser.parse_args()
    rendered = table()
    if not args.write:
        print(rendered)
        return
    for path in (ROOT / 'README.md', ROOT / 'docs/commands.md'):
        content = path.read_text(encoding='utf-8')
        if content.count(START) != 1 or content.count(END) != 1:
            raise ValueError(f'Expected one catalog marker pair: {path}')
        left, remainder = content.split(START)
        _, right = remainder.split(END)
        path.write_text(left + START + '\n' + rendered + '\n' + END + right, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
