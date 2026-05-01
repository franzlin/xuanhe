"""
《宣和二年》补全增强模块
涵盖5项简化系统的补全
"""
import random

# ============================
# 1. 性格维度行为后果
# ============================

PERSONALITY_IMPACT = {
    "义利": {
        "重利轻义": {"社交修正": -1, "NpcTrust": "低", "叙事": "此人行事总以利字当头"},
        "义利兼顾": {"社交修正": 0, "NpcTrust": "中", "叙事": "利害之间，尚能权衡"},
        "重义轻利": {"社交修正": 1, "NpcTrust": "高", "叙事": "一诺千金，言而有信"},
    },
    "刚柔": {
        "刚硬": {"冲突修正": 1, "谈判修正": -1, "叙事": "宁折不弯，行事果决"},
        "刚柔并济": {"冲突修正": 0, "谈判修正": 0, "叙事": "刚柔之间，分寸恰好"},
        "柔和": {"冲突修正": -1, "谈判修正": 1, "叙事": "以柔克刚，不与人争"},
    },
    "宽狭": {
        "宽厚": {"原谅概率": 0.6, "记仇概率": 0.1, "叙事": "胸怀宽广，不计前嫌"},
        "宽严适中": {"原谅概率": 0.3, "记仇概率": 0.3, "叙事": "恩怨分明"},
        "狭窄": {"原谅概率": 0.05, "记仇概率": 0.7, "叙事": "睚眦必报，寸步不让"},
    },
    "胆勇": {
        "胆怯": {"冒险修正": -1, "抗压修正": -1, "叙事": "行事谨慎，不越雷池"},
        "胆勇适中": {"冒险修正": 0, "抗压修正": 0, "叙事": "胆识俱佳"},
        "勇猛": {"冒险修正": 1, "抗压修正": 1, "叙事": "浑身是胆，敢作敢当"},
    },
}


def classify_personality_level(dim_name, value):
    """根据数值归类性格档位"""
    if dim_name == "义利":
        if value <= -10:
            return "重利轻义"
        elif value <= 10:
            return "义利兼顾"
        return "重义轻利"
    elif dim_name == "刚柔":
        if value <= -10:
            return "刚硬"
        elif value <= 10:
            return "刚柔并济"
        return "柔和"
    elif dim_name == "宽狭":
        if value <= -10:
            return "宽厚"
        elif value <= 10:
            return "宽严适中"
        return "狭窄"
    elif dim_name == "胆勇":
        if value <= -10:
            return "胆怯"
        elif value <= 10:
            return "胆勇适中"
        return "勇猛"
    return "中正"


def get_personality_bonus(player, dim_name, action_type):
    """获取性格维度对行动类型的修正"""
    if dim_name not in ("yili_actions", "gangrou_actions", "kuanxia_actions", "danyong_actions"):
        return 0

    # 根据action_type判断适用哪个维度
    dim_map = {
        "义利": "yili_actions", "刚柔": "gangrou_actions",
        "宽狭": "kuanxia_actions", "胆勇": "danyong_actions",
    }

    real_dim = None
    for d, key in dim_map.items():
        if dim_name == key:
            real_dim = d
            break

    if not real_dim:
        return 0

    # 获取当前档位
    if real_dim == "义利":
        cumulative = player.get("yili_actions", 0)
    elif real_dim == "刚柔":
        cumulative = player.get("gangrou_actions", 0)
    elif real_dim == "宽狭":
        cumulative = player.get("kuanxia_actions", 0)
    else:
        cumulative = player.get("danyong_actions", 0)

    level = classify_personality_level(real_dim, cumulative)
    impact = PERSONALITY_IMPACT.get(real_dim, {}).get(level, {})

    # 映射修正
    if action_type in ("社交", "风月", "功名"):
        return impact.get("社交修正", 0)
    elif action_type in ("战斗", "犯罪"):
        return impact.get("冲突修正", 0) or impact.get("冒险修正", 0)
    elif action_type in ("经营", "研发"):
        return impact.get("谈判修正", 0) or 0
    return 0


# ============================
# 2. 经营市场环境联动
# ============================

MARKET_CONDITIONS = {
    "方腊起事_东南": {"丝价": "涨三成", "茶价": "涨两成", "粮价": "涨两成"},
    "宋金开战_边境": {"马价": "断供", "铁价": "涨三成", "粮价": "涨两成"},
    "漕运阻滞_京城": {"粮价": "涨一档", "酒成本": "涨一档"},
    "秋收_丰年": {"粮价": "跌两成", "布价": "跌一成"},
    "花石纲_加征": {"丝价": "涨两成", "商税": "加两成"},
}


def get_market_impact(player):
    """获取当前市场环境对经营的影响"""
    current_time = player.get("current_time", "宣和二年正月")
    conditions = []

    if "十月" in current_time or "十一月" in current_time or "十二月" in current_time or "宣和三年" in current_time:
        conditions.append(("方腊起事", MARKET_CONDITIONS["方腊起事_东南"]))

    if "宣和三年" in current_time or "宣和四年" in current_time:
        conditions.append(("宋金交兵", MARKET_CONDITIONS["宋金开战_边境"]))

    if random.random() < 0.2:
        conditions.append(("漕运阻滞", MARKET_CONDITIONS["漕运阻滞_京城"]))

    if any(w in current_time for w in ["八月", "九月", "十月"]) and random.random() < 0.3:
        conditions.append(("秋收丰年", MARKET_CONDITIONS["秋收_丰年"]))

    return conditions


def get_business_modifier_from_market(player, business_type):
    """根据市场环境获取经营修正"""
    conditions = get_market_impact(player)
    modifier = 1.0

    for name, impacts in conditions:
        if business_type in ("商铺", "行商") and "粮价" in impacts:
            mod_str = impacts["粮价"]
            if "涨" in mod_str:
                modifier += 0.1
        if business_type == "作坊" and "丝价" in impacts:
            modifier += 0.1
        if business_type == "田庄" and "秋收" in name:
            modifier += 0.15

    return modifier


# ============================
# 3. 科举备考期
# ============================

EXAM_PREP_ACTIONS = {
    "闭门攻读": {"精耗": 5, "属性": "intelligence", "效果": "经义造诣↑，健康↓"},
    "诗词唱和": {"精耗": 3, "金耗": 2, "属性": "charm", "效果": "文名↑，结识名士"},
    "策论演练": {"精耗": 4, "属性": "politics", "效果": "时务洞察↑"},
    "购书延师": {"精耗": 2, "金耗": 5, "效果": "备考资源↑"},
    "休沐调养": {"精耗": 2, "效果": "健康↑，精力微恢复"},
}

EXAM_PREP_EVENTS = [
    {"名称": "书坊新刻《三经新义》", "选项": ["倾囊购书", "借阅抄录", "专攻洛学"]},
    {"名称": "场屋病根初现", "选项": ["停药苦读", "购药静养", "游山水散心"]},
    {"名称": "太学清议雅集", "选项": ["附和新学", "直言民力", "沉默作诗"]},
    {"名称": "坊间押题秘卷", "选项": ["重金购入", "斥为伪书", "借观默记"]},
    {"名称": "偶遇退隐考官", "选项": ["恭敬请教", "试探行贿", "论道辩经"]},
]


def get_exam_prep_action(action_name):
    """获取备考行动详情"""
    return EXAM_PREP_ACTIONS.get(action_name)


def trigger_prep_event():
    """触发备考随机事件"""
    if random.random() < 0.2:
        return random.choice(EXAM_PREP_EVENTS)
    return None


def get_exam_debuff(health_level, consecutive_study_months):
    """获取考场debuff"""
    debuffs = []
    if health_level in ("病弱", "垂危"):
        debuffs.append("场屋病倒风险↑↑")
    elif health_level == "伤病":
        debuffs.append("头晕腹泻→发挥-1档")
    if consecutive_study_months >= 3:
        debuffs.append("连续苦读→场屋病根")
    return debuffs


# ============================
# 4. 暴露风险精细粒度
# ============================

EXPOSURE_INCREMENT = {
    "通奸": (15, 25),
    "私盐走私": (10, 20),
    "贪污受贿": (10, 25),
    "谋杀灭口": (30, 50),
    "伪造欺诈": (10, 15),
    "强占": (10, 20),
    "包庇": (5, 15),
}

EXPOSURE_THRESHOLDS = {
    "安全": (0, 30, "天衣无缝"),
    "风声": (31, 60, "市井已有流言"),
    "注意": (61, 80, "有司暗中查访"),
    "立案": (81, 100, "海捕文书/皇城司出动"),
}


def get_exposure_level(risk_value):
    """暴露风险值转定性档位"""
    for level, (lo, hi, narrative) in EXPOSURE_THRESHOLDS.items():
        if risk_value <= hi:
            return level, narrative
    return "立案", EXPOSURE_THRESHOLDS["立案"][2]


def add_exposure(current_risk, crime_type):
    """增加暴露风险（精细版）"""
    if crime_type not in EXPOSURE_INCREMENT:
        return current_risk

    lo, hi = EXPOSURE_INCREMENT[crime_type]
    increment = random.randint(lo, hi)
    new_risk = min(100, current_risk + increment)

    old_level, _ = get_exposure_level(current_risk)
    new_level, narrative = get_exposure_level(new_risk)

    if new_level != old_level:
        return new_risk, f"暴露风险升至「{new_level}」——{narrative}"
    return new_risk, ""


def decay_exposure(current_risk, months_no_crime=1):
    """暴露风险衰减"""
    if months_no_crime >= 1:
        decay = min(15, current_risk)
        return max(0, current_risk - 5 * months_no_crime)
    return current_risk


# ============================
# 5. 做官升迁磨勘机制
# ============================

PROMOTION_PATHS = {
    "进士出身": {
        "升迁速度": "快",
        "上限": "宰执",
        "路径": "知县→通判→知州→转运使→侍郎→尚书→宰执",
    },
    "荫补出身": {
        "升迁速度": "中",
        "上限": "侍郎",
        "路径": "县尉→知县→通判→知州→郎中→侍郎",
    },
    "吏员出身": {
        "升迁速度": "慢",
        "上限": "知州",
        "路径": "吏目→县尉→知县→通判→知州",
    },
    "其他": {
        "升迁速度": "极慢",
        "上限": "知县",
        "路径": "杂职→县尉→知县",
    },
}

OFFICIAL_RANKS_ORDER = [
    "白身", "吏目", "县尉", "知县", "通判",
    "知州", "转运使", "郎中", "侍郎", "尚书", "宰执"
]


def get_promotion_path(player):
    """获取玩家的升迁路径"""
    exam_score = int(player.get("exam_total_score", 0))
    if exam_score >= 100:
        return PROMOTION_PATHS["进士出身"]
    elif player.get("faction_alignment", ""):
        return PROMOTION_PATHS["荫补出身"]
    else:
        return PROMOTION_PATHS["吏员出身"]


def check_mokan_promotion(player, months_in_office):
    """
    磨勘考核（三年一考）
    返回: (是否晋升, 新官职, 描述)
    """
    if months_in_office < 36:
        return False, player.get("official_rank", "白身"), "任期未满三年"

    path = get_promotion_path(player)
    current_rank = player.get("official_rank", "白身")
    current_idx = OFFICIAL_RANKS_ORDER.index(current_rank) if current_rank in OFFICIAL_RANKS_ORDER else 0

    # 政绩判定（简化）
    politics = player.get("politics", "拙劣")
    prest_official = player.get("prestige_official", "默默无闻")

    base_prob = 0.4
    if politics in ("优良", "卓越"):
        base_prob += 0.2
    if prest_official in ("小有名气", "众望所归", "天下景仰"):
        base_prob += 0.15

    # 派系加成
    if player.get("faction_alignment") == "蔡党":
        base_prob += 0.15
    elif player.get("faction_alignment") == "帝党":
        base_prob += 0.05

    promoted = random.random() < base_prob

    if promoted:
        next_idx = min(current_idx + 1, len(OFFICIAL_RANKS_ORDER) - 1)
        new_rank = OFFICIAL_RANKS_ORDER[next_idx]

        # 非进士出身上限检查
        if player.get("exam_total_score", 0) < 100 and new_rank in ("尚书", "宰执"):
            new_rank = "侍郎"
        elif player.get("exam_total_score", 0) == 0 and new_rank in ("郎中", "侍郎"):
            new_rank = "知州"

        return True, new_rank, f"磨勘通过！晋升「{new_rank}」"
    else:
        return False, current_rank, "磨勘未过，原地留任"


def get_grey_income(official_rank, greed_level, power_level):
    """计算灰色收入"""
    rank_income = {
        "白身": 0, "吏目": 2, "县尉": 5, "知县": 10,
        "通判": 20, "知州": 40, "转运使": 80,
        "郎中": 120, "侍郎": 200, "尚书": 300, "宰执": 500,
    }
    base = rank_income.get(official_rank, 0)
    if greed_level == "高":
        base = int(base * 1.5)
    elif greed_level == "低":
        base = int(base * 0.3)
    return base
