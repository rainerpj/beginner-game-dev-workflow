"""Materialize three synthetic project walkthroughs and exercise the real state API.

No real customer, model interview, engine execution or game acceptance is claimed.
"""
from pathlib import Path
import json
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import workflow as w
import improvement

CASES = [
    dict(folder='动作', name='纸鸟送信', genre='横版平台跳跃', route='已有 Unity 2D 工程，先核对版本与输入/碰撞；不切换引擎',
         brief='玩家操纵纸鸟左右移动和跳跃，把信送到终点。Windows 键盘单人，已有 Unity 2D 工程；希望短关卡、有清楚的落点。不做战斗与故事分支。完整目标是三个关卡，不能只交一个测试场景。',
         question='跌落后，你希望回到本关起点，还是最近的检查点？', answer='回到本关起点，信件也重置。',
         loop='左右移动→观察落点→按跳跃跨过缺口→拾取信件→到达邮箱→结算并解锁下一关。',
         rule='地面接触时允许跳跃，空中不默认追加二段跳；一次投递只结算一次。跌落回本关起点并重置信件；暂定手感数值必须在实际运行后调整。',
         normal='带信接触邮箱，应只出现一次投递结果并解锁下一关；缺信不能完成投递。',
         failure='同帧多次接触邮箱不重复结算；跌落、重新开始后没有残留速度/重复信件；暂停恢复不穿透平台。',
         units=['关卡 1：基础跳跃与投递教学', '关卡 2：组合落点与信件路线', '关卡 3：综合挑战与最终完成画面'],
         assets='纸鸟与跳跃/落地动作、平台与邮箱、信件、UI 与跳跃/投递声音。',
         calibration='测量一个包含移动/跳跃/投递/跌落重试的代表关卡的制作、调手感与测试成本，再确认三个关卡的批量计划。',
         acceptance='从新游戏完成三个关卡，验证解锁、重开、适用存档、设置与退出；无叙事结局要求。'),
    dict(folder='解谜', name='灯塔电路', genre='机关解谜', route='已有 Godot 项目，先检查 project.godot、场景与信号；保留已有路线',
         brief='俯视二维灯塔，转动镜子让光线照到接收器。Windows 鼠标单人，现有 Godot 项目。每关可重置；完整范围暂定四个谜题。不做时间压力、战斗或随机生成。旧草稿写“不可撤销”，新版想给一次撤销。',
         question='新版“一次撤销”是否取代旧草稿的“不可撤销”，并且保留整关重置？', answer='按新版：可以撤销上一步，仍能整关重置。',
         loop='观察光源与接收器→旋转镜子→光路更新→接收器亮起→核对全部目标→进入下一谜题。',
         rule='按当前镜子状态计算光路，避免循环光路无限递归；达成全部目标才通关。撤销只回退最近一次有效转动，执行后没有第二步可撤销；无记录时按钮禁用。重置恢复本关初始配置并清空撤销记录。通关后停止镜子输入和撤销，显示下一关与重玩；重玩不撤回已解锁关卡。后两项是为边界完整性提出的 AI 草案，实际项目需结合体验确认。',
         normal='按有效解法转动镜子后全部接收器点亮，只触发一次通关；撤销后光路与关卡状态一致。',
         failure='顺序不同仍按实际布局判断；循环光路有终止条件；重复点击、无可撤销步骤、通关时撤销/重置都要有明确结果。',
         units=['谜题 1：转向与接收器教学', '谜题 2：两次反射', '谜题 3：顺序与目标组合', '谜题 4：综合解法'],
         assets='镜子/光源/接收器状态图、光线表现、撤销与重置按钮、通关反馈。',
         calibration='先完成一个同时覆盖通关、错误布局、撤销、重置的谜题，测量设计/解法验证与资源接入成本，再确认剩余谜题。',
         acceptance='四个谜题至少各有可执行解法，测试替代顺序和重置；可从开始走到完成并重新选择谜题，不强加剧情分支。'),
    dict(folder='经营', name='小小茶铺', genre='持续游玩的经营', route='无现成工程；先按二维界面、Windows 和现有工具提出方案，技术选型为 AI 建议，未伪造已创建工程',
         brief='单人经营茶铺，买原料、备茶、接待顾客和升级设备。Windows 鼠标二维界面，希望放松，无固定故事结局。初版两种饮品、一个商店场景、两个设备等级；希望能保存退出再继续，不做离线收益或联网。',
         question='原料不足时，你希望拒绝当前订单，还是允许等待补货后再制作？', answer='当前订单可以拒绝，不扣原料；不设倒计时。',
         loop='查看原料和资金→采购→接单→一次性消耗配方→制作与交付→收款→补货或升级→继续经营。',
         rule='下单并确认可制作时检查库存；扣料与制作状态一起提交，一单只收款一次。资金不足时购买失败且库存不变；无离线收益。保存包含库存、资金、设备和未完成订单状态。制作途中退出后恢复保存时的进度，已扣原料不再次扣除；已交付订单不重复收款。恢复细节为 AI 草案，需在实际项目中体验确认。',
         normal='原料足够时只扣一份配方并收一次款；保存退出重启后库存、资金和设备一致。',
         failure='原料不足时拒绝不扣料；快速多次点击不重复扣料/收款；缺钱时购买不成功；制作途中退出后按已约定状态恢复。',
         units=['饮品 A 的配方与订单', '饮品 B 的配方与订单', '两级设备及升级条件', '商店场景、经营目标与继续入口'],
         assets='原料/饮品图标、设备两个等级、订单状态 UI、资金库存文字与制作/收款声音。',
         calibration='先用一种饮品和一条资源链验证买料到收款、断货与存读档，再量测第二种饮品和升级系统的增量成本。',
         acceptance='两种饮品与两级设备全部可达，验证盈利和耗尽路径、保存退出恢复，以及完成首个经营目标后仍可继续；不添加强制结局。'),
]


def run(root):
    if root.exists():
        raise ValueError('Keep prior walkthrough output; choose an unused directory.')
    root.mkdir(parents=True)
    results = []
    for case in CASES:
        folder = root / case['folder']
        records = folder / '项目记录'; records.mkdir(parents=True)
        stamp = '# 合成项目走查 · 不是客户项目或游戏运行证据\n\n'
        def write(name, body):
            path = folder / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(stamp + body.strip() + '\n', encoding='utf-8')
        write('00_客户资料/测试输入.md', '# 原始测试设定\n\n' + case['brief'] + '\n\n## 后续脚本化回答\n' + case['answer'])
        write('项目记录/资料接收与理解.md', '# 已读取资料\n\n来源：00_客户资料/测试输入.md“原始测试设定”全文。\n' + case['brief'] + '\n\n当前必要问题：' + case['question'] + '\n按脚本化回答处理：' + case['answer'] + '\n没有把其他类型的证件、工作日或剧情结局加入本案。')
        write('项目记录/项目概念.md', f"# {case['name']}\n\n[Confirmed in fixture] 主要玩法：{case['genre']}。平台和范围来源见测试输入。\n\n技术路线：{case['route']}。\n\n没有实际打开游戏工程；测试环境只生成工作流记录。")
        write('项目记录/游戏设计.md', f"# 规则草案\n\n## 核心循环\n{case['loop']}\n\n## 状态与边界\n{case['rule']}\n\n## 正常验收\n{case['normal']}\n\n## 异常与恢复\n{case['failure']}\n\n## 完整体验\n{case['acceptance']}\n\n规则依据为脚本化测试输入；手感、难度和好玩程度待真实游戏验证。")
        write('项目记录/完整版本范围.md', '# 范围与成本\n\n测试输入指定的完整内容：\n' + '\n'.join('- ' + x for x in case['units']) + '\n\n正式资源：' + case['assets'] + '\n\n产品配套：开始/继续、教学、设置、退出，适用的存档、暂停与恢复；目标环境独立运行、交付说明与维护交接。\n\n完整验收：' + case['acceptance'] + '\n\n暂定制作计划，不承诺工期。' + case['calibration'] + '\n实际成本尚未测量，S4 后再作批量确认。')
        write('项目记录/内容与资产矩阵.md', '# 内容到任务\n\n| 内容 | 制作任务 | 验收入口 |\n|---|---|---|\n' + '\n'.join(f'| {unit} | T52 | 用规则草案中正常/异常用例逐项检查 |' for unit in case['units']) + '\n| 产品配套 | T51 | 新开局、恢复、退出与重新进入 |\n\nT52 是待细分的首批制作任务，依赖代表片段 T41；T50 汇总验收依赖真实批次，不能反过来。')
        write('项目记录/功能任务单.md', f"# T31 核心循环\n\n可见结果：{case['loop']}\n\n包含：一个最小内容单元及错误、重试路径；不包含全量内容。\n前置：T30 实际工程与运行环境、T21 需求拆分。\n验收：{case['normal']}\n{case['failure']}\n\n当前无游戏工程产物，操作入口待 T30 核验后填写；不能凭文档标记完成。")
        write('项目记录/当前操作/设计.md', '# T10–T21 设计走查卡\n\n本步只让设定、规则和完整范围可审阅。AI 读取测试输入并写记录；模拟参与者按脚本回答缺口。\n\n1. 打开项目记录/游戏设计.md，检查玩家动作和失败结果。\n2. 对照完整版本范围.md，检查内容是否等于测试输入，是否出现未经选择的功能。\n3. 在反馈中指出问题；回答未处理前不验收。\n\n这些文件现在真实存在，但它们不是游戏。下一步由 AI 核对实际引擎及工程入口。')
        write('项目记录/当前操作/工程.md', '# T30 工程准备卡\n\nAI 先核对：' + case['route'] + '。\n\n当前这个隔离夹具没有真实游戏工程或引擎运行证据。参与者此时无需点不存在的场景。应继续收集实际工程位置/工具条件，具备条件后补准确启动步骤与观察结果。\n\nT30 保持 blocked；T31 不能验收。缺引擎期间可继续审阅设计和素材来源，不能说已编译。')
        write('项目记录/当前操作/批次.md', '# T52 首批内容\n\n依赖 T41 代表片段、真实样本成本与范围复核。当前不进入制作。\n正式开始前按内容矩阵把每个内容 ID 对应到真实资产和测试入口；实现后核对正常、失败与恢复，再登记实际运行证据。')
        write('项目记录/走查证据.md', '# 流程夹具证据\n\n由脚本合成客户角色的回答与设计审阅，只用于测试状态门槛。未执行任何游戏或实际客户验收。\n同一 AI 对上述具体文档进行正确性与必要性检查，结果与限制见本目录复查记录。')
        state = w.seed(); path = records / 'state.json'; w.atomic(path, state)
        w.atomic(records / '工作流改进.json', improvement.seed())
        def apply(**kw):
            nonlocal state
            state = w.apply(dict(revision=state['revision'], **kw), path, folder)
            return state
        def evidence(kind):
            return dict(kind=kind, result='pass', path='项目记录/走查证据.md', note='仅合成流程证据，非真实客户/游戏验收', by='pilot fixture', at=w.now())
        reviews = {key: dict(result='pass', path='项目记录/走查证据.md', note='合成流程自查', by='pilot fixture', at=w.now()) for key in ('correctness','necessity')}
        apply(op='project', title=case['name'], direction=case['genre'], reason='隔离走查的测试输入')
        for tid in ('T00', 'T01'):
            apply(op='update',task=tid,instructions='项目记录/当前操作/设计.md',status='done',evidence=[evidence('document')],reviews=reviews)
        apply(op='update',task='T10',instructions='项目记录/当前操作/设计.md',status='active',question=case['question'])
        try:
            apply(op='update',task='T10',status='done',evidence=[evidence('document'),evidence('customer')],reviews=reviews)
            raise AssertionError('Question gate was bypassed')
        except w.Invalid as exc:
            assert '等待客户决定' in str(exc)
        apply(op='feedback',task='T10',kind='idea',text='合成回答：'+case['answer'])
        fid=state['feedback'][-1]['id']
        apply(op='resolve',feedback=fid,resolution='脚本化答案已用于设计草案，真实客户尚未参与')
        apply(op='update',task='T10',question='')
        for tid in ('T10','T11','T20','T21'):
            apply(op='update',task=tid,instructions='项目记录/当前操作/设计.md',status='done',evidence=[evidence('document'),evidence('customer')],reviews=reviews)
        apply(op='update',task='T30',instructions='项目记录/当前操作/工程.md',status='blocked',blocker='隔离流程夹具未提供真实工程/引擎运行，不能生成游戏运行证据')
        apply(op='update',task='T31',instructions='项目记录/功能任务单.md',goal=case['loop'])
        try:
            apply(op='update',task='T31',status='done',evidence=[evidence('document')],reviews=reviews)
            raise AssertionError('Missing runtime gate was bypassed')
        except w.Invalid as exc:
            assert '引擎/开发环境实际运行验证' in str(exc)
        apply(op='add',item=dict(id='T52',stage='S5',title=case['name']+'首批内容',goal='按内容矩阵逐项实现，不把原型当完整游戏',depends=['T41'],required=['document','editor'],instructions='项目记录/当前操作/批次.md'))
        w.validate(state,folder)
        taskmap={t['id']:t for t in w.view(state,folder)['tasks']}
        assert taskmap['T30']['status']=='blocked' and not taskmap['T31']['accepted']
        assert 'T52' in taskmap['T50']['effective_depends'] and 'T50' not in taskmap['T52']['effective_depends']
        results.append(dict(case=case['folder'],project=case['name'],revision=state['revision'],
                            question_gate='pass',feedback_answer='pass',runtime_gate='pass',batch_dependency='pass',
                            limitation='synthetic walkthrough only; no real customer or engine'))
    (root/'执行结果.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':
    run(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else APP.parent/'07_示例与交付验收/V0.4试用走查')
