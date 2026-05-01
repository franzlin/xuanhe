"""
《宣和二年》风月/后宫/姻缘系统（完整合一版）
对齐《核心机制》§八、魅力属性系统、后官妃嫔、子嗣孕产全部章节
"""
import random
import json

# ============================
# 风月场所（深度交互版）
# ============================

PLEASURE_VENUES = {
    "樊楼": {
        "desc": "汴京第一酒楼，名妓云集，朝野权贵出入频繁",
        "cost": (5, 20),
        "risk": 0.20,
        "互动": {
            "打茶围": {"精耗": 3, "效果": "人品风味尽显，结识名士/探听朝野消息", "情报品": "可信"},
            "重金包妓": {"精耗": 4, "效果": "独占花魁一夜，减压↑↑", "情报品": "可信", "条件": "金≥20贯"},
            "只赏曲不涉风月": {"精耗": 2, "效果": "文雅之举，文名微↑", "情报品": "传闻"},
            "暗中打探": {"精耗": 4, "效果": "借酒色之便套话，情报↑", "情报品": "可信", "风险": "对方警觉"},
        },
    },
    "勾栏行院": {
        "desc": "瓦舍中的风月场所，鱼龙混杂，三教九流出没",
        "cost": (2, 10),
        "risk": 0.30,
        "互动": {
            "随意消遣": {"精耗": 2, "效果": "减压为主", "情报品": "传闻"},
            "结交行首": {"精耗": 4, "效果": "结识行院头牌，获市井情报", "情报品": "可信"},
            "参与酒令": {"精耗": 3, "效果": "融入市井圈，获江湖名微↑", "情报品": "传闻"},
        },
    },
    "茶坊": {
        "desc": "清雅茶肆，可听曲谈心，偶遇墨客名流",
        "cost": (1, 5),
        "risk": 0.08,
        "互动": {
            "清茶听曲": {"精耗": 2, "效果": "修身养性，文名微↑"},
            "约谈交心": {"精耗": 3, "效果": "与NPC深谈，好感↑机会", "情报品": "可信"},
            "品茗论道": {"精耗": 3, "效果": "雅集交流，结识文士", "情报品": "可信"},
        },
    },
}

# ============================
# 情缘/红颜知己
# ============================

COURTESAN_TEMPLATES = [
    {"艺名": "柳如是", "技艺": "琴箫", "性情": "温婉清冷", "身世": "家道中落的官宦之后"},
    {"艺名": "苏卿卿", "技艺": "词曲", "性情": "洒脱豪放", "身世": "原为江南歌伎"},
    {"艺名": "玉楼春", "技艺": "琵琶", "性情": "精明细心", "身世": "被嫡母卖入青楼"},
    {"艺名": "顾横波", "技艺": "诗词书画", "性情": "端庄大气", "身世": "失怙后卖艺为生"},
    {"艺名": "沈婉儿", "技艺": "舞", "性情": "娇媚灵动", "身世": "灾年流落汴京"},
]

SWEETHEART_LEVELS = {
    "初识": {"好感度": 0, "可做": ["清茶听曲", "约谈交心"], "侍奉概率": 0},
    "相熟": {"好感度": 20, "可做": ["约谈交心", "品茗论道", "打茶围"], "侍奉概率": 0.1},
    "红颜知己": {"好感度": 50, "可做": ["约谈交心", "重金包妓", "暗中打探"], "侍奉概率": 0.3},
    "倾心": {"好感度": 80, "可做": ["共度良宵", "代为打探", "赎回从良"], "侍奉概率": 0.6},
    "死心塌地": {"好感度": 150, "可做": ["共度良宵", "代为打探", "赎身纳妾", "传密信"], "侍奉概率": 0.9},
}


def visit_pleasure(player, venue_name="樊楼", interaction="打茶围"):
    """风月行动（完整版）返回多维结果"""
    venue = PLEASURE_VENUES.get(venue_name, PLEASURE_VENUES["樊楼"])
    actions = venue.get("互动", {})
    action = actions.get(interaction, actions.get("打茶围", {"精耗": 3, "效果": "", "情报品": "传闻"}))

    cost = random.randint(*venue["cost"])
    if interaction == "重金包妓":
        cost = max(20, cost * 2)
    elif interaction == "清茶听曲":
        cost = min(cost, random.randint(1, 3))

    charm = player.get("charm", "普通")
    charm_bonus = {"拙劣": -2, "平庸": -1, "普通": 0, "优良": 1, "卓越": 2}.get(charm, 0)

    # 情报获取
    intel_quality = action.get("情报品", "传闻")
    intel_gain = random.randint(0, 2) + max(0, charm_bonus)

    # 社交影响
    bond_change = random.randint(-1, 1) + charm_bonus
    prest_change = 0
    if interaction == "只赏曲不涉风月":
        prest_change = 1
    elif interaction == "品茗论道":
        prest_change = random.randint(0, 1)

    # 风险
    risk_event = None
    if random.random() < venue["risk"]:
        risks = [
            "被老鸨讹诈，多花了5贯",
            "被官差盘问，惹了麻烦",
            "染了暗疾，身体微恙",
            "官声受损，被同僚风言风语",
            "偶遇政敌，场面尴尬",
        ]
        risk_event = random.choice(risks)
        if "多花" in risk_event:
            cost += 5
        if "官声" in risk_event:
            prest_change -= 1

    result = {
        "venue": venue_name,
        "interaction": interaction,
        "cost": cost,
        "intel_gain": intel_gain,
        "intel_quality": intel_quality,
        "bond_change": bond_change,
        "prestige_change": prest_change,
        "risk_event": risk_event,
        "charm_bonus": charm_bonus,
    }

    # 叙事
    desc = f"于{venue_name}{interaction}，花费{cost}贯"
    if intel_gain > 0:
        desc += "，席间听得一些风声"
    if prest_change > 0:
        desc += "，众人称赞雅量"
    if risk_event:
        desc += f"。{risk_event}"
    result["description"] = desc
    return result


# ============================
# 后宫系统（完整版）
# ============================

HAREM_RANKS = [
    "采女", "宝林", "御女", "才人", "美人", "婕妤",
    "嫔", "昭仪", "妃", "贵妃", "皇贵妃", "皇后"
]

FAVOR_LEVELS = {
    "冷落":   {"min": 0, "max": 50, "侍寝概率": 0.05, "宫人态度": "敷衍推脱", "月例": 2},
    "寻常":   {"min": 50, "max": 150, "侍寝概率": 0.15, "宫人态度": "寻常服侍", "月例": 5},
    "得宠":   {"min": 150, "max": 300, "侍寝概率": 0.35, "宫人态度": "殷勤周到", "月例": 15},
    "专宠":   {"min": 300, "max": 450, "侍寝概率": 0.60, "宫人态度": "百般奉承", "月例": 30},
    "祸水":   {"min": 450, "max": 500, "侍寝概率": 0.80, "宫人态度": "言听计从", "月例": 50},
}

FULL_HAREM_ACTIONS = {
    "妆扮候驾": {"精耗": 4, "效果": "等待临幸，恩宠↑0~3"},
    "圣前献艺": {"精耗": 5, "效果": "展示才艺，恩宠↑1~5"},
    "探望皇后": {"精耗": 3, "效果": "维系后宫关系，皇后好感↑"},
    "结交宫人": {"精耗": 3, "效果": "赏赐宫人，打通关节"},
    "焚香修道": {"精耗": 2, "效果": "明哲保身，暂避宫斗"},
    "打探宫闱": {"精耗": 3, "效果": "刺探高位妃嫔动向"},
    "进献补品": {"精耗": 2, "效果": "讨好官家，恩宠微↑", "条件": "金≥5贯"},
    "拉拢太监": {"精耗": 3, "效果": "收买黄门做内应", "条件": "金≥10贯"},
}


def get_favor_level(favor_value):
    for level, info in FAVOR_LEVELS.items():
        if favor_value <= info["max"]:
            return level, info
    return "祸水", FAVOR_LEVELS["祸水"]


def change_favor(current_favor, delta, reason="日常"):
    new_favor = max(0, min(500, current_favor + delta))
    old_level, _ = get_favor_level(current_favor)
    new_level, info = get_favor_level(new_favor)
    if new_level != old_level:
        desc = f"恩宠升至「{new_level}」——{reason}" if delta > 0 else f"恩宠降至「{new_level}」——{reason}"
    else:
        desc = f"恩宠{delta:+d}（{new_level}）——{reason}"
    return new_favor, new_level, desc


def harem_action(player, action_type, current_favor=50, current_rank_index=0):
    """后宫行动（妃嫔专属·完整版）"""
    rank = HAREM_RANKS[min(current_rank_index, len(HAREM_RANKS) - 1)]
    act = FULL_HAREM_ACTIONS.get(action_type, FULL_HAREM_ACTIONS["妆扮候驾"])

    # 条件检查
    if "条件" in act:
        cond = act["条件"]
        if "金≥" in cond:
            required = int(cond.replace("金≥", "").replace("贯", ""))
            if player.get("money", 0) < required:
                return {"error": f"金钱不足（需要{required}贯）"}

    # 恩宠变动
    charm = player.get("charm", "普通")
    favor_gain = random.randint(0, 3)
    if action_type == "圣前献艺":
        favor_gain = random.randint(1, 5)
        if charm in ("优良", "卓越"):
            favor_gain += 1
    elif action_type == "妆扮候驾":
        favor_gain = random.randint(0, 3)
        if charm in ("优良", "卓越"):
            favor_gain += 1
    elif action_type == "进献补品":
        favor_gain = random.randint(0, 2)
    elif action_type in ("探望皇后", "结交宫人"):
        favor_gain = random.randint(0, 2)

    new_favor, new_level, fav_desc = change_favor(current_favor, favor_gain, action_type)

    # 位份提升
    level_order = list(FAVOR_LEVELS.keys())
    rank_up = False
    if new_level != get_favor_level(current_favor)[0]:
        if favor_gain > 0:
            # 跨档可晋升
            rank_up = current_rank_index < len(HAREM_RANKS) - 2
            if rank_up:
                current_rank_index += 1
                rank = HAREM_RANKS[min(current_rank_index, len(HAREM_RANKS) - 1)]

    # 侍寝可能性
    serving_prob = FAVOR_LEVELS[new_level]["侍寝概率"]
    served = random.random() < serving_prob

    return {
        "action": act["效果"],
        "favor_gain": favor_gain,
        "new_favor": new_favor,
        "new_level": new_level,
        "energy_cost": act["精耗"],
        "current_rank": rank,
        "rank_index": current_rank_index,
        "rank_up": rank_up,
        "served_tonight": served,
        "fav_desc": fav_desc,
    }


# ============================
# 宫斗系统
# ============================

COURT_STRUGGLE = {
    "巫蛊厌胜": {
        "条件": "有道婆协助", "效果": 60,
        "败露概率": 0.35, "败露后果": "下狱论罪，最轻冷宫，最重赐死",
        "精耗": 6,
    },
    "饮食投毒": {
        "条件": "有内应（御膳房/宫人）", "效果": 100,
        "败露概率": 0.55, "败露后果": "绞，牵连九族",
        "精耗": 8,
    },
    "谣言中伤": {
        "条件": "有心腹太监", "效果": 30,
        "败露概率": 0.20, "败露后果": "降位，罚俸，禁足",
        "精耗": 4,
    },
    "争宠献艺": {
        "条件": "才艺技能≥优良", "效果": 40,
        "败露概率": 0.05, "败露后果": "表演失败，贻笑大方",
        "精耗": 5,
    },
}


def execute_court_struggle(method, player_alertness="低", player_yindu="中", has_insider=False):
    if method not in COURT_STRUGGLE:
        return False, 0, "未知手段", 0

    info = COURT_STRUGGLE[method]
    if method in ("巫蛊厌胜", "饮食投毒", "谣言中伤") and not has_insider:
        return False, 0, f"缺少必要条件：{info['条件']}", info["精耗"]

    fail_prob = info["败露概率"]
    if player_alertness == "高":
        fail_prob *= 1.2
    if player_yindu == "高":
        fail_prob *= 0.7

    if random.random() < fail_prob:
        return "败露", 0, info["败露后果"], info["精耗"]

    actual = int(info["效果"] * random.uniform(0.7, 1.3))
    return "成功", actual, f"手段奏效", info["精耗"]


# ============================
# 妊娠/产子/子嗣系统
# ============================

def pregnancy_check(age, favor_level, consecutive_served=0, palace_enemies=0):
    """妊娠检定"""
    if age <= 20:
        age_factor = 1.3
    elif age <= 28:
        age_factor = 1.0
    elif age <= 35:
        age_factor = 0.5
    else:
        age_factor = 0.15

    favor_factor = FAVOR_LEVELS.get(favor_level, FAVOR_LEVELS["冷落"])["侍寝概率"]
    freq_factor = min(1.0, consecutive_served * 0.15)

    preg_prob = age_factor * favor_factor * freq_factor * 0.3
    miscarriage_prob = min(0.5, palace_enemies * 0.05)

    if random.random() < preg_prob:
        if random.random() < miscarriage_prob:
            return "流产", 0, "不幸小产，身心俱创"
        return "怀孕", 10, "太医诊出喜脉！"

    return "未孕", 0, "本月未见喜讯"


def childbirth(mother_age, is_prince=True):
    """产子判定"""
    is_male = random.random() < 0.5
    danger = 0.02 + (0.05 if mother_age > 30 else 0) + (0.10 if mother_age > 38 else 0)
    mother_safe = random.random() > danger

    infanticide_prob = 0.10 if is_male and is_prince else 0.03
    child_safe = random.random() > infanticide_prob
    gender = "皇子" if is_male else "帝姬"

    if not mother_safe:
        return False, gender, "难产——母子危殆"
    if not child_safe:
        return True, gender, f"{gender}降生，然未及满月即夭折（疑遭暗害）"
    return True, gender, f"喜诞{gender}，母子平安！"


def create_child(name, gender, birth_month, is_prince=False):
    return {
        "name": name,
        "gender": gender,
        "birth_month": birth_month,
        "age": 0,
        "is_prince": is_prince,
        "health": "康健",
        "talent": random.choice(["聪颖", "平庸", "木讷", "伶俐", "早慧"]),
    }


def grow_children(children, current_month=""):
    """推进子嗣成长1月，返回发生的事件"""
    events = []
    for child in children:
        child["age"] = (child.get("age", 0) or 0)
        # 满15岁触发成年事件
        if child["age"] == 15:
            gender = child.get("gender", "")
            if gender == "皇子":
                events.append(f"{child['name']}年满十五，可行冠礼——朝中开始关注这位皇子")
            else:
                events.append(f"{child['name']}年满十五，及笄礼成——开始有世家提亲")
    return events


# ============================
# 姻缘事件池
# ============================

ROMANCE_EVENTS = [
    {
        "名称": "榜下捉婿",
        "触发": "科举放榜月+魅力≥普通",
        "描述": "放榜之日，权贵大门洞开，家丁守在榜下……",
        "选项": [
            {"选": "接受某家提亲", "效果": "绑定派系资源↑、获得聘礼"},
            {"选": "婉拒自立", "效果": "人望↑、自由"},
            {"选": "虚与委蛇拖延", "效果": "暂不得罪人"},
        ],
    },
    {
        "名称": "权贵逼迫献妾",
        "触发": "有权势者看上你的红颜知己",
        "描述": "{人物}派人暗示，想将{红颜}收入府中……",
        "选项": [
            {"选": "忍痛割爱", "效果": "获取政治资源、好感↑"},
            {"选": "断然拒绝", "效果": "得罪权贵、红颜好感↑↑"},
            {"选": "安排出逃", "效果": "精5+金20贯、保全情义"},
        ],
    },
    {
        "名称": "红颜有难",
        "触发": "你的红颜知己遭遇困境",
        "描述": "{红颜}传来消息，{事件}——急需帮助",
        "选项": [
            {"选": "全力相助", "效果": "精3+金10贯、红颜死心塌地"},
            {"选": "量力而为", "效果": "精1+金3贯、好感微升"},
            {"选": "无暇顾及", "效果": "好感↓"},
        ],
    },
    {
        "名称": "太后指婚",
        "触发": "后宫妃嫔+恩宠≥得宠",
        "描述": "太后传来懿旨，欲将某宗室女指给{人物}为妻/妾",
        "选项": [
            {"选": "谢恩接受", "效果": "太后好感↑↑、联姻↑"},
            {"选": "婉言辞谢", "效果": "风险：太后不悦"},
        ],
    },
]


def trigger_romance_event(player):
    """触发姻缘随机事件"""
    if random.random() < 0.15:
        event = random.choice(ROMANCE_EVENTS)
        return event["名称"], event
    return None, None


# ============================
# 辅助：子嗣数据存取
# ============================

def get_children(player):
    """获取玩家的子女列表"""
    children = player.get("children", "[]")
    if isinstance(children, str):
        try:
            children = json.loads(children)
        except (json.JSONDecodeError, TypeError):
            children = []
    return children


def save_children(player, children):
    """保存子女列表到player数据"""
    player["children"] = json.dumps(children, ensure_ascii=False)
    return player
