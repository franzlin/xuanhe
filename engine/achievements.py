"""
《宣和二年》排行/成就/回忆/纪念品系统
对齐《核心机制》§三十四

设计原则：
- 排行榜提供进度感和竞争参照
- 里程碑自动触发，记录关键人生节点
- 回忆系统在合适时机闪回过往经历
- 纪念品永久保留，触发回忆和好感加成
"""
import random
import json


# ============================
# 排行榜
# ============================

RANKING_DIMENSIONS = {
    "家产排名": {
        "数据来源": ["金钱", "产业估值"],
        "更新频率": "每季",
        "叙事模板": "{rank_desc}在{location}{rank_suffix}",
    },
    "权势排名": {
        "数据来源": ["权力值", "派系资源"],
        "更新频率": "每季",
        "叙事模板": "{rank_desc}在朝中{rank_suffix}",
    },
    "文名排名": {
        "数据来源": ["文名声望分项"],
        "更新频率": "每年",
        "叙事模板": "汴京文坛，{rank_desc}",
    },
    "江湖排名": {
        "数据来源": ["江湖名声望分项"],
        "更新频率": "每年",
        "叙事模板": "江湖中人提起足下，{rank_desc}",
    },
}

RANK_TIERS = {
    "top5": {"等级": "顶尖", "描述": "位列前五"},
    "top20": {"等级": "知名", "描述": "排名前二十"},
    "top50": {"等级": "中游", "描述": "位列中游"},
    "bottom": {"等级": "末流", "描述": "尚不显名"},
}


def evaluate_ranking(player, dimension):
    """评估玩家在某个维度的排名"""
    if dimension == "家产排名":
        money = int(player.get("money", 0))
        if money >= 5000:
            return RANK_TIERS["top5"]["描述"], "富甲一方"
        elif money >= 1000:
            return RANK_TIERS["top20"]["描述"], "家资殷实"
        elif money >= 200:
            return RANK_TIERS["top50"]["描述"], "小有积蓄"
        return RANK_TIERS["bottom"]["描述"], "囊中羞涩"

    elif dimension == "权势排名":
        power = player.get("power", "微末")
        power_order = ["微末", "小吏", "地方", "朝堂", "权倾"]
        try:
            idx = power_order.index(power)
        except ValueError:
            idx = 0
        tiers = [
            (4, "权倾朝野"),
            (3, "朝堂重臣"),
            (2, "一方大吏"),
            (1, "初入仕途"),
            (0, "白身布衣"),
        ]
        for threshold, desc in tiers:
            if idx >= threshold:
                return desc, desc
        return "微末", "微末"

    elif dimension == "文名排名":
        prestige_literary = player.get("prestige_literary", "默默无闻")
        lit_order = ["默默无闻", "小有名气", "众望所归", "天下景仰"]
        try:
            idx = lit_order.index(prestige_literary)
        except ValueError:
            idx = 0
        if idx >= 3:
            return "公认大家", "天下文宗"
        elif idx >= 2:
            return "文坛翘楚", "名满京华"
        elif idx >= 1:
            return "崭露头角", "文名初显"
        return "尚不显名", "默默无闻"

    elif dimension == "江湖排名":
        prestige_jianghu = player.get("prestige_jianghu", "默默无闻")
        jh_order = ["默默无闻", "小有名气", "众望所归", "天下景仰"]
        try:
            idx = jh_order.index(prestige_jianghu)
        except ValueError:
            idx = 0
        if idx >= 3:
            return "威震天下", "一方豪雄"
        elif idx >= 2:
            return "声名远播", "江湖皆知"
        elif idx >= 1:
            return "初露锋芒", "略有微名"
        return "无名之辈", "默默无闻"

    return "无法评估", ""


def format_ranking(dimension, player):
    """格式化排行描述"""
    rank_desc, suffix = evaluate_ranking(player, dimension)
    location = player.get("location", "东京开封府")
    info = RANKING_DIMENSIONS[dimension]
    template = info["叙事模板"]
    result = template.format(rank_desc=rank_desc, location=location, rank_suffix=suffix)
    return result


# ============================
# 里程碑系统
# ============================

MILESTONES = {
    "初入江湖": {
        "触发条件": lambda p, npcs: len(npcs) >= 3,
        "叙事模板": "{location}城中，已有人识得阁下",
    },
    "初试锋芒": {
        "触发条件": lambda p, npcs: p.get("high_value_actions", 0) >= 1,
        "叙事模板": "此役之后，你对自己有了新的认识",
    },
    "功名初就": {
        "触发条件": lambda p, npcs: p.get("official_rank", "白身") != "白身",
        "叙事模板": "一朝金榜题名，从此踏入官场",
    },
    "商海初成": {
        "触发条件": lambda p, npcs: int(p.get("money", 0)) >= 100,
        "叙事模板": "你的第一桶金，已在手中",
    },
    "患难之交": {
        "触发条件": lambda p, npcs: any(n.get("bond") == "至交" for n in npcs),
        "叙事模板": "此生得一知己，足矣",
    },
    "血海深仇": {
        "触发条件": lambda p, npcs: any(n.get("grudge_level") == "血仇" for n in npcs),
        "叙事模板": "从此，你的生命中多了一份无法释怀的恨",
    },
    "父亲母亲": {
        "触发条件": lambda p, npcs: len(p.get("children", [])) > 0,
        "叙事模板": "初为人父/母，你的人生翻开了新的一页",
    },
}


def check_milestones(player, npcs, existing_milestones=None):
    """
    检查里程碑触发
    返回: 新触发的里程碑列表
    """
    if existing_milestones is None:
        existing_milestones = []

    if isinstance(existing_milestones, str):
        try:
            existing_milestones = json.loads(existing_milestones)
        except (json.JSONDecodeError, TypeError):
            existing_milestones = []

    new_milestones = []
    for name, info in MILESTONES.items():
        if name in existing_milestones:
            continue
        if info["触发条件"](player, npcs):
            location = player.get("location", "东京开封府")
            narrative = info["叙事模板"].format(location=location)
            new_milestones.append({"名称": name, "叙事": narrative, "触发时间": player.get("current_time", "")})

    return new_milestones


# ============================
# 回忆系统
# ============================

MEMORY_TRIGGERS = {
    "地点关联": {
        "条件": "重返曾发生重大事件的地点",
        "示例": "重返杭州→\"三年前你在此救下书生...\"",
    },
    "人物关联": {
        "条件": "再次遇见久别的关键NPC",
        "示例": "再遇初恋→\"十年前的那个春天...\"",
    },
    "时间关联": {
        "条件": "特定纪念日/节气",
        "示例": "中秋→\"去年中秋，你与李纲对月畅饮...\"",
    },
    "物品关联": {
        "条件": "使用/看到与旧事相关的物品",
        "示例": "看到端砚→\"这方砚台让你想起了...\"",
    },
}

# 回忆模板
MEMORY_TEMPLATES = [
    "此时此刻，你忽然想起{time}在{location}，{event}——那时你还{description}。",
    "物是人非。{time}之前，你曾在{location}{event}，如今{current_situation}。",
    "一阵恍惚。{time}的{location}，{event}，仿佛昨日。",
    "不知为何，脑中浮现{time}在{location}的情景：{event}。",
]


def generate_memory(player, milestone):
    """根据里程碑生成回忆文本"""
    if not milestone:
        return None

    template = random.choice(MEMORY_TEMPLATES)
    return template.format(
        time=milestone.get("触发时间", "从前"),
        location=player.get("location", "某地"),
        event=milestone.get("叙事", ""),
        description="初涉世事" if "初" in milestone.get("名称", "") else "已非当日",
        current_situation="想来已是陈年旧事",
    )


# ============================
# 纪念品系统
# ============================

KEEPSAKE_TYPES = {
    "定情信物": {"效果": "重逢时关联NPC好感+1，触发回忆"},
    "战利品": {"效果": "持有者武名+1级印象，可触发战斗回忆"},
    "恩赏之物": {"效果": "持有者官声+1级印象，不可出售"},
    "故人之物": {"效果": "查看时自动生成1段回忆叙事"},
}


def create_keepsake(name, keepsake_type, related_npc="", story=""):
    """创建纪念品"""
    if keepsake_type not in KEEPSAKE_TYPES:
        keepsake_type = "故人之物"

    return {
        "category": "特殊道具",
        "name": name,
        "tags": ["纪念", keepsake_type],
        "status": "永久保留",
        "detail": story,
        "related_npc": related_npc,
        "is_keepsake": True,
    }
