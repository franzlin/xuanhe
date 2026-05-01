"""
《宣和二年》后宫深度系统 (Harem/Palace System)
对齐《核心机制》§八

设计原则：
- 恩宠0-500五档制（冷落/寻常/得宠/专宠/祸水）
- 妊娠机制：临幸频率+年龄系数+后宫仇恨干预
- 产子：皇子/帝姬，皇子风险更高
- 宫斗手段：巫蛊/投毒/谣言/献艺+败露概率
- 宫斗后果：降位/冷宫/赐死
"""
import random


# ============================
# 恩宠系统
# ============================

FAVOR_LEVELS = {
    "冷落": {"min": 0, "max": 50, "侍寝概率": 0.05, "宫人态度": "敷衍推脱"},
    "寻常": {"min": 50, "max": 150, "侍寝概率": 0.15, "宫人态度": "寻常服侍"},
    "得宠": {"min": 150, "max": 300, "侍寝概率": 0.35, "宫人态度": "殷勤周到"},
    "专宠": {"min": 300, "max": 450, "侍寝概率": 0.60, "宫人态度": "百般奉承"},
    "祸水": {"min": 450, "max": 500, "侍寝概率": 0.80, "宫人态度": "言听计从"},
}


def get_favor_level(favor_value):
    """根据恩宠数值确定档位"""
    for level, info in FAVOR_LEVELS.items():
        if favor_value <= info["max"]:
            return level, info
    return "祸水", FAVOR_LEVELS["祸水"]


def change_favor(current_favor, delta, reason="日常"):
    """恩宠变动，返回(新值, 新档位, 描述)"""
    new_favor = max(0, min(500, current_favor + delta))
    old_level, _ = get_favor_level(current_favor)
    new_level, info = get_favor_level(new_favor)

    if new_level != old_level:
        if delta > 0:
            desc = f"恩宠升至「{new_level}」——{reason}"
        else:
            desc = f"恩宠降至「{new_level}」——{reason}"
    else:
        desc = f"恩宠{delta:+d}（{new_level}）——{reason}"

    return new_favor, new_level, desc


# ============================
# 宫斗手段
# ============================

COURT_STRUGGLE = {
    "巫蛊厌胜": {
        "条件": "有道婆协助",
        "效果": 60,  # 对方恩宠降值
        "败露概率": 0.35,
        "败露后果": "下狱论罪，最轻冷宫，最重赐死",
    },
    "饮食投毒": {
        "条件": "有内应（御膳房/宫人）",
        "效果": 100,  # 对方生病或死亡
        "败露概率": 0.55,
        "败露后果": "绞，牵连九族",
    },
    "谣言中伤": {
        "条件": "有心腹太监",
        "效果": 30,  # 对方恩宠降值
        "败露概率": 0.20,
        "败露后果": "降位，罚俸，禁足",
    },
    "争宠献艺": {
        "条件": "才艺技能≥优良",
        "效果": 40,  # 自身恩宠升值
        "败露概率": 0.05,
        "败露后果": "表演失败，贻笑大方",
    },
}


def execute_court_struggle(method, player_alertness="低", player_yindu="中", has_insider=False):
    """
    执行宫斗手段
    返回: (成功/败露, 效果值, 描述)
    """
    if method not in COURT_STRUGGLE:
        return False, 0, "未知手段"

    info = COURT_STRUGGLE[method]

    # 检查条件
    if method == "巫蛊厌胜" and not has_insider:
        return False, 0, "需要道婆协助，无人可用"
    if method == "饮食投毒" and not has_insider:
        return False, 0, "需要在御膳房有内应"
    if method == "谣言中伤" and not has_insider:
        return False, 0, "需要有心腹太监散布谣言"
    if method == "争宠献艺" and player_alertness == "高":
        pass  # 高警惕可略降败露概率

    # 败露概率修正
    fail_prob = info["败露概率"]
    if player_alertness == "高":
        fail_prob *= 1.2  # 对方警惕高则败露概率升
    if player_yindu == "高":
        fail_prob *= 0.7  # 自己阴毒高则败露概率降

    if random.random() < fail_prob:
        return "败露", 0, info["败露后果"]

    # 效果随机波动
    base_effect = info["效果"]
    actual_effect = int(base_effect * random.uniform(0.7, 1.3))
    return "成功", actual_effect, f"手段奏效，效果{actual_effect:+d}"


# ============================
# 妊娠与产子
# ============================

def pregnancy_check(age, favor_level, consecutive_months=1, palace_hatred=0):
    """
    妊娠检定
    consecutive_months: 连续临幸月数
    palace_hatred: 后宫仇恨总和（影响流产概率）
    返回: (是否怀孕, 流产概率, 描述)
    """
    # 年龄系数
    if age <= 20:
        age_factor = 1.3
    elif age <= 28:
        age_factor = 1.0
    elif age <= 35:
        age_factor = 0.6
    else:
        age_factor = 0.2

    # 恩宠系数
    level_info = FAVOR_LEVELS.get(favor_level, FAVOR_LEVELS["冷落"])
    favor_factor = level_info["侍寝概率"]

    # 临幸频率
    freq_factor = min(1.0, consecutive_months * 0.15)

    pregnancy_prob = age_factor * favor_factor * freq_factor * 0.3

    # 后宫仇恨增加流产概率
    miscarriage_prob = min(0.5, palace_hatred * 0.05)

    if random.random() < pregnancy_prob:
        if random.random() < miscarriage_prob:
            return False, miscarriage_prob, "不幸小产，身心俱创"
        return True, miscarriage_prob, "太医诊出喜脉！"

    return False, miscarriage_prob, "本月未见喜讯"


def childbirth(player_age, is_prince=True):
    """
    产子判定
    返回: (母子是否平安, 孩子性别, 描述)
    """
    # 性别概率：约50/50
    is_male = random.random() < 0.5

    # 母亲健康风险（年龄越大风险越高）
    danger_prob = 0.02
    if player_age > 30:
        danger_prob += 0.05
    if player_age > 38:
        danger_prob += 0.10

    mother_safe = random.random() > danger_prob

    # 皇子被谋害概率显著高于帝姬
    infanticide_prob = 0.10 if is_male and is_prince else 0.03 if not is_male else 0.02

    child_safe = random.random() > infanticide_prob

    gender = "皇子" if is_male else "帝姬"

    if not mother_safe:
        return False, gender, "难产——母子危殆"
    if not child_safe:
        return True, gender, f"{gender}降生，然未及满月即夭折（疑遭暗害）"
    return True, gender, f"喜诞{gender}，母子平安！"


# ============================
# 后宫月度事件
# ============================

PALACE_MONTHLY_EVENTS = {
    "高位妃嫔刁难": {
        "触发条件": "恩宠≥得宠",
        "选项": [
            {"选项": "忍气吞声", "效果": "恩宠微降、对方减缓"},
            {"选项": "反唇相讥", "效果": "恩宠微升但树敌"},
            {"选项": "向官家哭诉", "效果": "恩宠+1档、对方被罚"},
        ],
    },
    "宫女泄露私密": {
        "触发条件": "有隐私把柄",
        "选项": [
            {"选项": "重金封口", "效果": "金-20贯、风险暂消"},
            {"选项": "杀鸡儆猴", "效果": "阴毒↑、宫人畏服"},
            {"选项": "转移话题", "效果": "风险仍在"},
        ],
    },
    "太医入宫诊脉": {
        "触发条件": "每月概率0.15",
        "选项": [
            {"选项": "接受诊脉", "效果": "获知身体状况"},
            {"选项": "婉拒", "效果": "无变化"},
            {"选项": "私下请太医", "效果": "金-5贯、获养生建议"},
        ],
    },
    "太后召见": {
        "触发条件": "恩宠≥得宠+年龄≤30",
        "选项": [
            {"选项": "恭谨应对", "效果": "太后好感↑、恩宠微升"},
            {"选项": "借机告状", "效果": "太后介入、可能帮倒忙"},
        ],
    },
}


def trigger_palace_event(favor_level):
    """触发后宫月度随机事件"""
    if random.random() < 0.3:
        event_pool = ["太医入宫诊脉"]
        if favor_level in ("得宠", "专宠", "祸水"):
            event_pool.append("高位妃嫔刁难")
            event_pool.append("太后召见")
        event_pool.append("宫女泄露私密")

        event_name = random.choice(event_pool)
        return event_name, PALACE_MONTHLY_EVENTS.get(event_name, {})

    return None, None
