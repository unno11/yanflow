"""Lightweight offline checks for this skill; Python standard library only."""
from __future__ import annotations

from pathlib import Path
import re
import sys


def check(root: Path) -> list[str]:
    errors = []
    main = root / 'SKILL.md'
    if not main.is_file():
        return ['SKILL.md is missing']
    content = main.read_text(encoding='utf-8')
    front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', content, re.S)
    if not front:
        errors.append('SKILL.md frontmatter is missing')
    else:
        for key in ['name', 'description']:
            match = re.search(r'^' + key + r':\s*(.+)$', front.group(1), re.M)
            if not match or not match.group(1).strip(' \"\''):
                errors.append(f'Frontmatter {key} must be nonempty')
        match = re.search(r'^name:\s*([a-z0-9-]+)\s*$', front.group(1), re.M)
        if not match or len(match.group(1)) > 64:
            errors.append('Skill name must use lowercase letters, digits or hyphens, <=64 characters')
    paths = [main, root/'README.md', *sorted((root/'references').glob('*.md'))]
    for path in paths:
        if not path.is_file():
            errors.append(f'Missing {path.relative_to(root)}')
            continue
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            link = link.strip('<>')
            if re.match(r'^[a-z][a-z0-9+.-]*:', link, re.I):
                continue
            target = link.split('#', 1)[0]
            if target and not (path.parent / target).exists():
                errors.append(f'{path.relative_to(root)}: broken link {link}')
    return errors


def main() -> None:
    errors = check(Path(__file__).resolve().parents[1])
    if errors:
        print('\n'.join(errors))
        sys.exit(1)
    print('PASS: skill metadata and local instruction links (lightweight check).')


if __name__ == '__main__':
    main()
