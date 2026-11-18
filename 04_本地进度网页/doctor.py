"""Read-only environment inspection except a self-cleaning write probe."""
import json
from pathlib import Path
import sys
import tempfile
import workflow
import improvement


def inspect(root):
    report = dict(scope='当前运行电脑；不代表客户电脑或游戏测试', python=sys.version.split()[0], executable=sys.executable, root=str(root), checks={}, capabilities={})
    checks = report['checks']
    checks['python_3_10_plus'] = sys.version_info >= (3, 10)
    for name in ('AGENTS.md', '项目记录/state.json'):
        try:
            (root / name).read_text(encoding='utf-8-sig')
            checks[name] = True
        except OSError as exc:
            checks[name] = str(exc)
    try:
        with tempfile.TemporaryDirectory(prefix='workflow-probe-', dir=root) as folder:
            probe = Path(folder) / 'probe.txt'
            probe.write_text('workflow write probe', encoding='utf-8')
            checks['write_read'] = probe.read_text(encoding='utf-8') == 'workflow write probe'
    except OSError as exc:
        checks['write_read'] = str(exc)
    try:
        state = workflow.read_json(root / '项目记录/state.json')
        workflow.validate(state, root)
        checks['state_structure'] = True
        report['revision'] = state['revision']
        report['accepted_tasks_needing_review'] = [t['id'] for t in workflow.view(state, root)['tasks'] if t['attention']]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks['state_structure'] = str(exc)
    try:
        improvement.validate(improvement.load(root), root)
        checks['improvement_structure'] = True
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks['improvement_structure'] = str(exc)
    report['capabilities'] = {key:'待 AI 按实际工具和操作验证' for key in ('Codex协作', '联网参考', '图像生成', '音频生产', '所选引擎或开发环境运行', '目标设备运行', '浏览器反馈同步')}
    game = root / 'Game'
    markers = []
    if all((game / name).is_dir() for name in ('Assets', 'Packages', 'ProjectSettings')):
        markers.append('Unity')
    if list(game.glob('*.uproject')):
        markers.append('Unreal')
    if (game / 'project.godot').is_file():
        markers.append('Godot')
    if (game / 'package.json').is_file():
        markers.append('JavaScript 项目（需核对是否为 Cocos/网页游戏及实际入口）')
    if (game / 'index.html').is_file():
        markers.append('HTML 入口（需核对实际用途）')
    report['game_root_structure'] = bool(markers)
    report['game_markers'] = markers
    report['game_note'] = '只检查 Game 根目录标识，不选择引擎或判断已安装。其他位置由 AI 核对；未找到工程不妨碍资料与设计阶段，找到标识也不代表能运行。'
    report['ok'] = all(value is True for value in checks.values())
    return report


if __name__ == '__main__':
    result = inspect(workflow.ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 1)
