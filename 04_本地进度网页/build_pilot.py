"""Build a clean new-project pilot ZIP from an explicit source allowlist.

Never copies live customer records or performs git/network operations.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'V0.4-pilot.1'
PACKAGE = '游戏开发工作流_' + VERSION
SKILLS = ('beginner-game-guide', 'beginner-game-design', 'beginner-game-programming',
          'beginner-unity-2d', 'beginner-game-art', 'beginner-game-reference',
          'beginner-game-review', 'beginner-workflow-improve')
SOURCE_FILES = (
    'AGENTS.md', 'README.md', '先看这里.txt', '启动进度网页.cmd', 'start_progress.py', 'python-required.txt',
    '00_客户资料/请把资料放在这里.md', '03_Skills/使用说明.md',
    '06_推进提示词库/使用说明.md', 'docs/V0.4试用交付说明.md',
    '07_示例与交付验收/V0.4试用验收.md', '07_示例与交付验收/多类型引导示例.md',
    '04_本地进度网页/workflow.py', '04_本地进度网页/workflow.json',
    '04_本地进度网页/improvement.py', '04_本地进度网页/server.py',
    '04_本地进度网页/doctor.py', '04_本地进度网页/init_project.py',
    '04_本地进度网页/使用说明.md', '04_本地进度网页/prompts.json',
    '04_本地进度网页/web/index.html', '04_本地进度网页/web/app.js',
    '04_本地进度网页/web/style.css', '04_本地进度网页/tests/check_package.py',
    '04_本地进度网页/tests/test_workflow.py', '04_本地进度网页/tests/test_improvement.py',
    '04_本地进度网页/tests/test_pilot.py', '04_本地进度网页/tests/browser.cjs',
)


def source_files(root):
    paths = set(SOURCE_FILES)
    for directory in ('01_客户指南', '02_工作流规范', '05_项目模板'):
        paths.update(p.relative_to(root).as_posix() for p in (root / directory).rglob('*.md')
                     if not p.is_symlink() and not any(x.startswith('.') for x in p.relative_to(root).parts))
    # Historical developer scope log; not instructions for a new customer.
    paths.discard('02_工作流规范/需求与交付目录.md')
    for name in SKILLS:
        base = root / '.agents/skills' / name
        paths.add((base / 'SKILL.md').relative_to(root).as_posix())
        paths.update(p.relative_to(root).as_posix() for p in (base / 'references').glob('*.md'))
    for ref in paths:
        path = root / ref
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Missing or unsafe package source: ' + ref)
    return sorted(paths)


def assemble(root, target):
    if target.exists():
        raise ValueError('Staging destination must not already exist.')
    refs = source_files(root)
    target.mkdir(parents=True)
    for ref in refs:
        dest = target / ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / ref, dest)
        if not dest.is_file():
            raise ValueError('Copy did not create: ' + ref)
    result = subprocess.run([sys.executable, '-B', str(target / '04_本地进度网页/init_project.py')],
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise ValueError('Clean initialization failed: ' + result.stderr)
    handoff = '''# 新项目交接 · V0.4-pilot.1

这是干净试用包，尚未接收本客户设定，也没有游戏成果或验收。
先读 AGENTS.md、项目记录/项目概念.md、state.json 和工作流改进.json。
提醒客户提供已有资料；没有资料也可开始。核对本机工具能力和真实工程。
当前下一步是项目记录/当前操作/T00_准备协作.md。先完成打开说明、状态同步、真实反馈与答复的小闭环；不能把页面能打开当作客户验收。
游戏类型未预设；已确定的方向从客户资料提取。缺游戏引擎不阻断资料与设计。
全部基线任务未开始，模板不是成果。收到客户实际决定后再更新需求与任务。
工作流本身的本机验证范围见 07_示例与交付验收/V0.4试用验收.md；不能用来登记本客户游戏已运行。
'''
    (target / 'docs/CODEX_HANDOFF.md').write_text(handoff, encoding='utf-8')
    return refs


def verify_clean(target):
    def read(ref): return json.loads((target / ref).read_text(encoding='utf-8-sig'))
    state = read('项目记录/state.json')
    ledger = read('项目记录/工作流改进.json')
    if state['revision'] != 0 or state['feedback'] or state['events'] or len(state['tasks']) != 20:
        raise ValueError('Package contains live game history.')
    if any(t['status'] != 'pending' or t['evidence'] or t['reviews'] or t['history'] for t in state['tasks']):
        raise ValueError('Package contains game acceptance records.')
    if ledger['revision'] != 0 or ledger['signals'] or ledger['items'] or ledger['reviews'] or ledger['events']:
        raise ValueError('Package contains developer improvement history.')
    if not (target / state['tasks'][0]['instructions']).is_file():
        raise ValueError('Missing first action card.')
    disallowed = {'.git', '__pycache__', 'backups', '变更备份', '发布记录', '交付包', 'Game'}
    for path in target.rglob('*'):
        if disallowed.intersection(path.relative_to(target).parts) or path.name.endswith(('.pyc', '.tmp', '.lock')):
            raise ValueError('Unexpected private or generated file: ' + str(path))
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '交付包' / (PACKAGE + '.zip'))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Output already exists; retain it and choose another filename.')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep staging outside the source tree so it can never be recursively packaged.
    with tempfile.TemporaryDirectory(prefix='workflow-pilot-build-') as tmp:
        target = Path(tmp) / PACKAGE
        sources = assemble(ROOT, target)
        # Python initialization may make caches; prevent them at process startup instead.
        verify_clean(target)
        manifest = dict(version=VERSION, source='local working tree; not a committed release',
                        game_status='fresh pending tasks; no customer evidence', source_files=sources,
                        files=sorted(p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()))
        manifest['files'].append('版本说明.json')
        manifest['files'].sort()
        (target / '版本说明.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(target / '04_本地进度网页/tests/check_package.py')],
                                capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            raise ValueError('Packaged document check failed: ' + result.stdout + result.stderr)
        with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
            for ref in manifest['files']:
                archive.write(target / ref, PACKAGE + '/' + ref)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP CRC check failed.')
            if set(archive.namelist()) != {PACKAGE + '/' + ref for ref in manifest['files']}:
                raise ValueError('ZIP file list mismatch.')
        print(json.dumps(dict(zip=str(output), files=len(manifest['files']), clean=True,
                              checks=json.loads(result.stdout)), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
