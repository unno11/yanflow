"""Initialize separate shared literature and project folders; preserve existing files."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re

TEMPLATES = Path(__file__).resolve().parents[1] / 'assets' / 'templates'
PROJECT_FILES = {
    'AGENTS.md': 'AGENTS.md',
    'handoff.md': 'handoff.md',
    'brainstorm.md': 'brainstorm.md',
    'related_work/index.md': 'related-work-index.md',
    'experiment/results.md': 'results.md',
    'experiment/evaluation.md': 'evaluation.md',
    'dataset.md': 'dataset.md',
    'learning.md': 'learning.md',
}
ENTRYPOINT_FILES = {'claude': 'CLAUDE.md', 'gemini': 'GEMINI.md'}


def render(template: str, values: dict[str, str]) -> str:
    source = (TEMPLATES / template).read_text(encoding='utf-8')
    return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values[m.group(1)], source)


def initialize(library_dir: Path, project_dir: Path | None = None,
               name: str | None = None, goal: str = '待与用户确定',
               terms: str = '待按领域确定',
               entrypoints: tuple[str, ...] = ()) -> list[dict[str, str]]:
    unknown = set(entrypoints) - ENTRYPOINT_FILES.keys()
    if unknown:
        raise ValueError(f'未知入口类型：{sorted(unknown)}')
    if entrypoints and project_dir is None:
        raise ValueError('创建工具入口需要指定独立项目目录。')
    library_dir = library_dir.expanduser().resolve()
    project_dir = project_dir.expanduser().resolve() if project_dir else None
    if project_dir == library_dir:
        raise ValueError('统一文献库与科研项目必须使用不同目录。')
    values = {
        'LIBRARY_DIR': library_dir.as_posix(),
        'LIBRARY_INDEX': (library_dir / 'index.md').as_posix(),
        'DATE': date.today().isoformat(),
    }
    if project_dir:
        values.update(PROJECT_DIR=project_dir.as_posix(), PROJECT_NAME=name or project_dir.name,
                      GOAL=goal, TERMS=terms)
    # Prepare all content before creating any output.
    outputs = [(library_dir / 'index.md', render('library-index.md', values))]
    if project_dir:
        outputs += [(project_dir / target, render(template, values))
                    for target, template in PROJECT_FILES.items()]
        outputs += [(project_dir / ENTRYPOINT_FILES[kind], render('tool-entrypoint.md', values))
                    for kind in dict.fromkeys(entrypoints)]
    (library_dir / 'papers').mkdir(parents=True, exist_ok=True)
    if project_dir:
        for rel in ['related_work', '复现', 'experiment', 'DataSet']:
            (project_dir / rel).mkdir(parents=True, exist_ok=True)
    actions = []
    for path, content in outputs:
        try:
            with path.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(content)
            action = 'created'
        except FileExistsError:
            if not path.is_file() or path.is_symlink():
                raise ValueError(f'目标不是普通文件，未覆盖：{path}')
            action = 'kept-existing'
        actions.append({'path': str(path), 'action': action})
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library-dir', required=True, type=Path,
                        help='使用者已指定的统一文献库位置；首次使用先询问，不猜路径。')
    parser.add_argument('--project-dir', type=Path, help='可选；本次需要创建的独立项目目录。')
    parser.add_argument('--name', help='项目名称；省略时采用目录名称。')
    parser.add_argument('--goal', default='待与用户确定', help='用户已提供的研究目标。')
    parser.add_argument('--terms', default='待按领域确定', help='已知领域术语。')
    parser.add_argument('--entrypoint', action='append', choices=sorted(ENTRYPOINT_FILES), default=[],
                        help='可选且可重复；只补指定工具的短入口，已有文件保留。')
    args = parser.parse_args()
    for item in initialize(args.library_dir, args.project_dir, args.name, args.goal, args.terms,
                           tuple(args.entrypoint)):
        print(f"{item['action']}: {item['path']}")


if __name__ == '__main__':
    main()
