"""
《宣和二年》风月权谋：通奸与勾引扩展系统 (§二十一)
将"色欲"与"权谋"深度绑定——低成本政治暗杀/商业垄断/情报获取
风险极高，收益极大
"""
import random

# ============================
# 目标分类与风险
# ============================
ADULTERY_TARGETS = {
    "官眷": {
        "典型": "蔡党侍郎妻、知州夫人",
        "勾引难度": "极难",
        "基准致死率": "极高",
        "权力碾压": "高",
        "权力劣势": "极高↑↑",
        "收益": "获取绝密奏札、操纵朝堂决策",
        "所需阶段": 4,
    },
    "富商妻": {
        "典型": "绸缎庄老板娘、盐商遗孀",
        "勾引难度": "困难",
        "基准致死率": "高",
        "权力碾压": "中",
        "权力劣势": "极高",
        "收益": "吞并产业、获取资金链",
        "所需阶段": 3,
    },
    "同僚/下属妻": {
        "典型": "县尉妻、衙役妇",
        "勾引难度": "普通",
        "基准致死率": "中",
        "权力碾压": "低",
        "权力劣势": "高",
        "收益": "控制下属、职场站队",
        "所需阶段": 3,
    },
    "尼姑/道姑": {
        "典型": "清修女冠、尼寺主持",
        "勾引难度": "困难",
        "基准致死率": "低",
        "权力碾压": "极低",
        "权力劣势": "中",
        "收益": "借神佛敛财、影响信徒",
        "所需阶段": 3,
    },
    "农妇/市井妇": {
        "典型": "佃户妻、酒肆老板娘",
        "勾引难度": "容易",
        "基准致死率": "低",
        "权力碾压": "极低",
        "权力劣势": "中",
        "收益": "零星财物、市井情报",
        "所需阶段": 2,
    },
}

# 勾引四阶段
SEDUCTION_STAGES = {
    1: {
        "名称": "窥视与铺路",
        "指令": ["物色目标", "重金贿赂其仆/媒婆", "施恩其夫/其家"],
        "判定属性": "智力+金钱+警惕",
        "成功标志": "获独处机会/对方回赠贴身物",
        "失败后果": "被丈夫察觉/被敲诈",
        "精耗": 3,
    },
    2: {
        "名称": "试探与逾矩",
        "指令": ["暗赠信物", "宴席间私语", "制造独处/救美机会"],
        "判定属性": "魅力+情报",
        "成功标志": "牵手/拥抱，对方默许",
        "失败后果": "被拒并声张→名望↓/被告官",
        "精耗": 4,
    },
    3: {
        "名称": "私通与控制",
        "指令": ["幽会", "许诺休妻/纳妾", "利用其夫"],
        "判定属性": "魅力+阴毒",
        "成功标志": "长期保持关系，获取情报/资源",
        "风险": "每次幽会通奸暴露+15~25",
        "精耗": 5,
    },
    4: {
        "名称": "事泄与善后",
        "触发": "暴露风险≥81 或 丈夫察觉 或 情妇反水",
        "选项": ["灭口", "构陷", "私了", "强压", "逃亡"],
        "精耗": 8,
    },
}

# 通奸专属指令
ADULTERY_ACTIONS = {
    "重金买通丫鬟": {"精耗": 3, "金耗": 5, "成功": "获知女主人行踪/喜好", "失败": "被告密，丈夫上门"},
    "借庙会灯会接近": {"精耗": 4, "金耗": 1, "成功": "搭讪成功留印象", "失败": "丈夫陪同无法近身"},
    "赠珠玉华服": {"精耗": 2, "金耗": 10, "成功": "对方收下并回礼", "失败": "被拒收训斥→人望↓"},
    "伪造其夫书信": {"精耗": 5, "金耗": 2, "成功": "骗出妇人幽会", "失败": "识破笔迹→报官"},
    "许诺正室之位": {"精耗": 0, "金耗": 0, "成功": "妇人死心塌地→谋杀亲夫", "失败": "事泄后被反咬→定罪强奸"},
    "夜半翻墙幽会": {"精耗": 5, "金耗": 0, "成功": "私通成功→情报↑", "失败": "被当场捉奸→打残/送官"},
}


# 情妇极化状态
MISTRESS_POLARIZATION = {
    "甘为外室": {
        "触发": "幽会≥5次+魅优+赠礼多",
        "行为": "死心塌地，掩盖通奸，拒绝丈夫同房",
        "产子倾向": "偷生留后，毒杀亲夫",
    },
    "权谋共谋": {
        "触发": "利益绑定+政治≥优良",
        "行为": "通奸为晋升手段，极度理智",
        "产子倾向": "视子嗣为筹码",
    },
    "因爱生恨": {
        "触发": "玩家提分手+魅低+阴毒高",
        "行为": "主动向丈夫坦白报复",
        "产子倾向": "堕胎嫁祸/生下作证物",
    },
    "趋炎附势": {
        "触发": "玩家权力远超其夫",
        "行为": "逢场作戏，随时倒戈",
        "产子倾向": "留子嗣为长期饭票",
    },
}

# 丈夫反馈矩阵
HUSBAND_REACTIONS = {
    "暴怒寻仇": {
        "条件": "刚烈+智低+无贪欲",
        "行为": "捉奸/买凶/告官",
        "子嗣处理": "强迫堕胎/溺婴",
    },
    "隐忍不言": {
        "条件": "玩家权力≥地方+胆小",
        "行为": "装作不知，疏远妻子",
        "子嗣处理": "默认亲子，抚养",
    },
    "敲诈勒索": {
        "条件": "贪欲≥高+阴毒≥中",
        "行为": "撞破索要封口费",
        "子嗣处理": "视出价决定",
    },
    "借种生子": {
        "条件": "丈夫无子+玩家卓越+重宗祧",
        "行为": "主动安排幽会→默许通奸",
        "子嗣处理": "欣然认领",
    },
    "献妻求荣": {
        "条件": "贪欲极高+玩家权倾",
        "行为": "主动献妻→撮合",
        "子嗣处理": "攀附权贵投名状",
    },
}

# 子嗣归属选项
CHILD_FATE = {
    "认祖归宗": {"效果": "断绝公开关系，子嗣归夫家", "风险": "未来可能反噬"},
    "狸猫换太子": {"效果": "玩家血脉入主正室，继承家业", "风险": "极高：败露→两族倾覆"},
    "暗养外室": {"效果": "子嗣随玩家姓，无宗族名分", "风险": "母子成软肋"},
    "掐死/溺婴": {"效果": "消除隐患", "风险": "情妇黑化↑↑/杀人罪证"},
}

# 事件池
ADULTERY_EVENTS = [
    {"名称": "借伞/借物还物", "选项": ["附情诗", "只还物", "赠更贵重"]},
    {"名称": "丈夫突然折返", "选项": ["跳窗逃跑", "藏于床底", "持械对峙"]},
    {"名称": "情妇以怀孕要挟", "选项": ["买药堕胎", "许诺迎娶", "杀人灭口"]},
    {"名称": "情妇反咬强奸", "选项": ["拿信物自证", "重金贿赂", "杀人灭口"]},
    {"名称": "枕边风请求", "选项": ["答应办事", "拒绝", "虚与委蛇"]},
    {"名称": "另一权贵亦看中此女", "选项": ["决斗比试", "主动退出", "陷害情敌"]},
    {"名称": "丫鬟撞破私情", "选项": ["收为同谋", "灭口", "威吓"]},
    {"名称": "药迷其夫", "选项": ["只求一晌", "趁机杀夫", "迷药是假的"]},
    {"名称": "旧情人重逢", "选项": ["再续前缘", "一刀两断", "利用旧情"]},
    {"名称": "丈夫中毒暴毙", "选项": ["调查洗嫌", "嫁祸他人", "携款潜逃"]},
]


def start_seduction(target_type, player_power, player_intelligence, player_charm):
    """开始勾引（阶段1判定）"""
    if target_type not in ADULTERY_TARGETS:
        return {"error": "无效目标类型"}

    target = ADULTERY_TARGETS[target_type]
    difficulty = target["勾引难度"]
    diff_map = {"容易": 0.7, "普通": 0.5, "困难": 0.3, "极难": 0.15}

    base_prob = diff_map.get(difficulty, 0.3)
    if player_intelligence in ("优良", "卓越"):
        base_prob += 0.1
    if player_charm in ("优良", "卓越"):
        base_prob += 0.1

    success = random.random() < base_prob
    if success:
        return {
            "stage": 2,
            "desc": f"物色{target_type}成功——{target['典型']}似有回应。进入阶段2：试探与逾矩。",
            "target": target_type,
        }
    else:
        return {
            "stage": 1,
            "desc": f"初次接触{target_type}失败。对方丈夫似有察觉。",
            "exposure": 10,
            "target": target_type,
        }


def advance_seduction(stage, player_charm, player_yindu, player_power, husband_power):
    """推进勾引阶段"""
    if stage >= 4:
        return {"stage": 4, "desc": "事泄！必须善后——灭口/构陷/私了/强压/逃亡"}

    stage_info = SEDUCTION_STAGES[stage]
    base_prob = 0.5 - (stage - 1) * 0.1

    if player_charm in ("优良", "卓越"):
        base_prob += 0.1
    if player_yindu == "高":
        base_prob += 0.05

    exposure = 0
    if stage == 3:
        # 幽会暴露
        exposure = random.randint(15, 25)
        if player_power >= husband_power:
            exposure = max(5, exposure - 10)

    success = random.random() < base_prob
    return {
        "stage": stage + 1 if success else stage,
        "success": success,
        "desc": stage_info["成功标志"] if success else stage_info["失败后果"],
        "exposure": exposure,
    }


def get_husband_reaction(husband_personality, player_power_value, has_children):
    """丈夫反应判定"""
    gangrou = husband_personality.get("gangrou", 50) if husband_personality else 50
    intelligence = husband_personality.get("intelligence", "普通") if husband_personality else "普通"
    greed = husband_personality.get("greed", "中") if husband_personality else "中"

    if gangrou >= 80 and intelligence in ("拙劣", "平庸") and greed == "低":
        return "暴怒寻仇"
    elif player_power_value >= 3 and gangrou <= 40:
        return "隐忍不言"
    elif greed == "高":
        return "敲诈勒索"
    elif not has_children and player_power_value >= 3:
        if random.random() < 0.3:
            return "借种生子"
    elif greed == "高" and player_power_value >= 4:
        if random.random() < 0.2:
            return "献妻求荣"
    return "暴怒寻仇"


def trigger_adultery_event(player_stage):
    """触发通奸随机事件"""
    if random.random() < 0.25:
        event = random.choice(ADULTERY_EVENTS)
        return event["名称"], event["选项"]
    return None, None


def get_polarization_state(mistress, player_charm, player_yindu, player_power_vs_husband):
    """判定情妇极化状态"""
    encounters = mistress.get("encounters", 0)
    if encounters >= 5 and player_charm in ("优良", "卓越"):
        return "甘为外室"
    elif player_yindu == "高" and player_power_vs_husband >= 2:
        return "权谋共谋"
    elif mistress.get("rejected", False) and player_charm in ("拙劣", "平庸") and player_yindu == "高":
        return "因爱生恨"
    elif player_power_vs_husband >= 3:
        return "趋炎附势"
    return "趋炎附势"
