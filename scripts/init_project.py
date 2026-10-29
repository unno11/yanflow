"""Initialize separate shared literature and project folders; preserve existing files."""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
import re
import subprocess
from socket import gethostname

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
DIRECTORY_ALIASES = {
    'experiment': ('experiments',),
    'related_work': ('related-work',),
    '复现': ('reproduction', 'reproductions'),
    'DataSet': ('datasets', 'data'),
}


def tracking_status(project_dir: Path, path: Path) -> str:
    """Report ignore status only; never stage files or edit ignore rules."""
    try:
        result = subprocess.run(
            ['git', '-C', str(project_dir), 'check-ignore', '--quiet', '--no-index',
             '--', str(path)], capture_output=True, timeout=5)
        return {0: 'ignored-local-only', 1: 'not-ignored'}.get(result.returncode, 'unverified')
    except (OSError, subprocess.TimeoutExpired):
        return 'unverified'


def render(template: str, values: dict[str, str]) -> str:
    source = (TEMPLATES / template).read_text(encoding='utf-8')
    return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values[m.group(1)], source)


def initialize(library_dir: Path | None = None, project_dir: Path | None = None,
               name: str | None = None, goal: str = '待与用户确定',
               terms: str = '待按领域确定',
               entrypoints: tuple[str, ...] = (), *, entrypoints_only: bool = False,
               main_record: Path | None = None, handoff_record: Path | None = None,
               maintainer: str = '待指定',
               constraints: tuple[str, ...] = ()) -> list[dict[str, str]]:
    unknown = set(entrypoints) - ENTRYPOINT_FILES.keys()
    if unknown:
        raise ValueError(f'未知入口类型：{sorted(unknown)}')
    if library_dir is None and project_dir is None:
        raise ValueError('至少指定文献库或项目目录之一。')
    if (entrypoints or entrypoints_only or main_record or handoff_record or constraints) and project_dir is None:
        raise ValueError('创建工具入口需要指定独立项目目录。')
    if (main_record or handoff_record or constraints) and not entrypoints_only:
        raise ValueError('外部记录与约束摘要须配合 --entrypoints-only，避免创建平行主纲。')
    if entrypoints_only and library_dir is not None:
        raise ValueError('仅补入口模式不创建文献库；需要时另行建立。')
    library_dir = library_dir.expanduser().resolve() if library_dir else None
    project_dir = project_dir.expanduser().resolve() if project_dir else None
    if library_dir is not None and project_dir == library_dir:
        raise ValueError('统一文献库与科研项目必须使用不同目录。')
    for record in (main_record, handoff_record):
        if record is not None and not record.expanduser().is_file():
            raise ValueError(f'记录文件不存在或当前不可访问，未写入：{record}')
    if project_dir and not entrypoints_only:
        for standard, aliases in DIRECTORY_ALIASES.items():
            if not (project_dir / standard).exists():
                matches = [alias for alias in aliases if (project_dir / alias).is_dir()]
                if matches:
                    raise ValueError(f'{standard} 发现可能等价目录 {matches}；先与使用者选择映射，'
                                     '不要新建近似名目录。已有项目可用 --entrypoints-only。')
    values = {
        'LIBRARY_DIR': library_dir.as_posix() if library_dir else '可选，未建立',
        'LIBRARY_REFERENCE': ('主机：`' + gethostname() + '`；路径：`' + (library_dir / 'index.md').as_posix()
                              + '`，其他工具可访问性待核实。') if library_dir else '可选，未建立。',
        'DATE': date.today().isoformat(),
        'UPDATED': datetime.now().astimezone().isoformat(timespec='seconds'),
        'HOST_ID': gethostname(),
        'MAINTAINER': maintainer,
        'MAIN_RECORD': main_record.expanduser().resolve().as_posix() if main_record else '未指定，待接入现有主纲',
        'HANDOFF_RECORD': (handoff_record.expanduser().resolve().as_posix() if handoff_record
                           else '未指定；读取项目现有交接，位置待核实'),
        'CONSTRAINTS': '\n'.join('- ' + c for c in constraints) if constraints else '- 尚未提供摘要；读取主纲核实，不推断额外权限。',
    }
    if project_dir:
        values.update(PROJECT_DIR=project_dir.as_posix(), PROJECT_NAME=name or project_dir.name,
                      GOAL=goal, TERMS=terms)
    # Prepare all content before creating any output.
    outputs = [(library_dir / 'index.md', render('library-index.md', values))] if library_dir else []
    if project_dir:
        if entrypoints_only:
            outputs.append((project_dir / 'AGENTS.md', render('project-entrypoint.md', values)))
        else:
            outputs += [(project_dir / target, render(template, values))
                        for target, template in PROJECT_FILES.items()]
        outputs += [(project_dir / ENTRYPOINT_FILES[kind], render('tool-entrypoint.md', values))
                    for kind in dict.fromkeys(entrypoints)]
    # Reject incompatible file targets before any creation.
    for path, _ in outputs:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f'目标不是普通文件，未覆盖：{path}')
    tracking = {path: tracking_status(project_dir, path) for path, _ in outputs
                if project_dir and path.is_relative_to(project_dir)}
    if library_dir:
        (library_dir / 'papers').mkdir(parents=True, exist_ok=True)
    if project_dir:
        project_dir.mkdir(parents=True, exist_ok=True)
        if not entrypoints_only:
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
        item = {'path': str(path), 'action': action}
        if project_dir and path.is_relative_to(project_dir):
            item['tracking'] = tracking[path]
        actions.append(item)
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library-dir', type=Path,
                        help='可选；仅本次需要文献库时询问或建立，不猜路径。')
    parser.add_argument('--project-dir', type=Path, help='可选；本次需要创建的独立项目目录。')
    parser.add_argument('--name', help='项目名称；省略时采用目录名称。')
    parser.add_argument('--goal', default='待与用户确定', help='用户已提供的研究目标。')
    parser.add_argument('--terms', default='待按领域确定', help='已知领域术语。')
    parser.add_argument('--entrypoint', action='append', choices=sorted(ENTRYPOINT_FILES), default=[],
                        help='可选且可重复；只补指定工具的短入口，已有文件保留。')
    parser.add_argument('--entrypoints-only', action='store_true', help='只补AGENTS及指定工具入口，不建骨架或文献库。')
    parser.add_argument('--main-record', type=Path, help='现有主纲的位置；配合仅补入口模式。')
    parser.add_argument('--handoff-record', type=Path, help='现有交接的位置；配合仅补入口模式。')
    parser.add_argument('--maintainer', default='待指定', help='主纲维护者或负责会话。')
    parser.add_argument('--constraint', action='append', default=[], help='可重复；用户已有硬约束的摘要，不用于新增授权。')
    args = parser.parse_args()
    try:
        actions = initialize(args.library_dir, args.project_dir, args.name, args.goal, args.terms,
                             tuple(args.entrypoint), entrypoints_only=args.entrypoints_only,
                             main_record=args.main_record, handoff_record=args.handoff_record,
                             maintainer=args.maintainer, constraints=tuple(args.constraint))
    except ValueError as exc:
        parser.error(str(exc))
    for item in actions:
        print(f"{item['action']}: {item['path']} [{item.get('tracking', 'not-applicable')}]")


if __name__ == '__main__':
    main()
