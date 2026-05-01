"""
《宣和二年》仇恨/恩怨系统 (Grudge System)
对齐《核心机制》§二十八

设计原则：
- 好感度=关系温度（冷热），仇恨=行动动机（会不会主动搞你）
- 两者独立但联动：好感=仇视时自动同步至grudges
- 三档仇恨各有不同的NPC报复行为和触发概率
"""
import random
import json


# ============================
# 仇恨三档体系
# ============================

GRUDGE_LEVELS = {
    "积怨": {
        "序": 1,
        "触发条件": ["单次失信", "轻微利益冲突", "派系摩擦"],
        "NPC行为": "被动不合作，推脱敷衍",
        "叙事呈现": "此人对你心存芥蒂",
    },
    "深仇": {
        "序": 2,
        "触发条件": ["重大利益受损", "当众侮辱", "背叛"],
        "NPC行为": "主动设障，暗中告密",
        "叙事呈现": "此人与你势不两立",
    },
    "血仇": {
        "序": 3,
        "触发条件": ["灭门级伤害", "杀亲", "抄家", "断子绝孙"],
        "NPC行为": "不择手段报复，生死不休",
        "叙事呈现": "此恨不共戴天",
    },
}

# 仇恨触发与升级规则
GRUDGE_TRIGGER = {
    "失信爽约": {"产生": "积怨", "好感变化": -7},
    "当众侮辱": {"产生": "深仇", "好感变化": -10, "宽狭低则升级": True},
    "重大利益侵害": {"产生": "深仇", "好感变化": -8, "亲属牵连则升级": "血仇"},
    "背叛告密": {"产生": "血仇", "好感变化": -18},
    "杀亲灭族": {"产生": "血仇", "好感变化": 0, "不可化解": True},
}

# NPC报复行为（过月触发）
GRUDGE_REVENGE = {
    "积怨": {
        "行为池": ["散布不利流言", "拒绝合作", "在公开场合冷言冷语"],
        "触发概率": 0.10,
        "事件规模": "小",
    },
    "深仇": {
        "行为池": [
            "暗中告密",
            "设局陷害",
            "拉拢敌对势力对付你",
            "向台谏递匿名状",
        ],
        "触发概率": 0.30,
        "事件规模": "中",
    },
    "血仇": {
        "行为池": [
            "买凶暗杀",
            "构陷谋反大罪",
            "倾家荡产买通死士",
            "联络你的所有敌人",
            "在朝堂上公开弹劾",
        ],
        "触发概率": 0.60,
        "事件规模": "大",
    },
}

# 化解方式
GRUDGE_RESOLUTION = {
    "积怨": {
        "方式": "赔礼道歉+金钱赔偿",
        "条件": "好感回升至≥寻常",
        "效果": "仇恨消除，恢复正常",
    },
    "深仇": {
        "方式1": {"方式": "替对方解决重大困难", "条件": "对方宽狭≥70或义利≥70", "效果": "仇恨降1档"},
        "方式2": {"方式": "交换人质/质押", "条件": "权力值≥对方", "效果": "仇恨冻结（不触发主动行为），但未消除"},
    },
    "血仇": {
        "方式": "不可化解",
        "例外": ["杀死对方", "永远回避", "对方宽狭极高+你救其性命"],
    },
}

# 仇恨传递规则
GRUDGE_TRANSMISSION = {
    "家族内传递": {
        "规则": "被害者的父母/兄弟/子女自动继承同档仇恨",
        "执行": "创建NPC时若标注家族关系，仇恨同步写入",
    },
    "派系同情": {
        "规则": "同派系NPC对仇恨对象好感-4",
        "执行": "融入派系动态，不触发主动报复",
    },
    "仇恨不跨派系": {
        "规则": "A派对玩家的仇恨不自动传递给B派",
        "例外": "仅当B派与A派有明确联盟时，B派NPC好感-2",
    },
}


def trigger_grudge(action_type, npc_name, npc_personality=None):
    """
    根据行动类型判断是否触发仇恨
    返回: (grudge_level, reason) 或 (None, None)
    """
    if action_type in GRUDGE_TRIGGER:
        info = GRUDGE_TRIGGER[action_type]
        level = info["产生"]

        # 宽狭低则升级（侮辱→深仇而非积怨）
        if npc_personality and info.get("宽狭低则升级"):
            kuanxia = npc_personality.get("kuanxia", 50)
            if kuanxia <= 30:
                level = "深仇"

        return level, action_type

    return None, None


def check_grudge_revenge(grudge_level):
    """过月时检查NPC是否会发起报复行动"""
    revenge_info = GRUDGE_REVENGE.get(grudge_level)
    if not revenge_info:
        return None

    if random.random() < revenge_info["触发概率"]:
        action = random.choice(revenge_info["行为池"])
        return {
            "行为": action,
            "规模": revenge_info["事件规模"],
        }
    return None


def get_narrative_hint(grudge_level):
    """获取仇恨的叙事暗示文本"""
    return GRUDGE_LEVELS.get(grudge_level, {}).get("叙事呈现", "")


def try_resolve_grudge(grudge_level, npc_personality=None, player_power="微末", npc_power="微末"):
    """尝试化解仇恨，返回可行的化解方案"""
    resolutions = []

    if grudge_level == "积怨":
        resolutions.append({"方式": "赔礼道歉", "消耗": "金5~20贯", "成功率": "高"})

    elif grudge_level == "深仇":
        if npc_personality:
            kuanxia = npc_personality.get("kuanxia", 50)
            yili = npc_personality.get("yili", 50)
            if kuanxia >= 70 or yili >= 70:
                resolutions.append({"方式": "替对方解决重大困难", "消耗": "精5+金/人情", "成功率": "中"})

        # 检查权力值比较
        power_order = ["微末", "小吏", "地方", "朝堂", "权倾"]
        try:
            player_idx = power_order.index(player_power)
            npc_idx = power_order.index(npc_power)
            if player_idx >= npc_idx:
                resolutions.append({"方式": "交换人质/质押", "消耗": "精3+派系资源", "成功率": "中"})
        except ValueError:
            pass

    elif grudge_level == "血仇":
        resolutions.append({"方式": "【不可化解】", "消耗": "-", "成功率": "0"})
        if npc_personality:
            kuanxia = npc_personality.get("kuanxia", 50)
            if kuanxia >= 85:
                resolutions.append({"方式": "救对方性命（极端情况）", "消耗": "精8+生命危险", "成功率": "极低"})

    return resolutions if resolutions else [{"方式": "常规交往化解", "消耗": "精3/月×3月", "成功率": "低"}]


def inherit_grudge_from_family(victim_name, victim_grudge_level, family_npcs):
    """
    家族仇恨传递：被害者的直系亲属自动继承同档仇恨
    family_npcs: {npc_name: relationship} 如 {"张三": "父", "李四": "子"}
    返回: {npc_name: grudge_level}
    """
    inherited = {}
    direct_relatives = {"父", "母", "子", "女", "兄", "弟", "姊", "妹"}
    for npc_name, relation in family_npcs.items():
        if relation in direct_relatives:
            inherited[npc_name] = victim_grudge_level
    return inherited


def grudge_to_tags(grudge_level):
    """仇恨档位转NPC tags"""
    tag_map = {
        "积怨": "心怀芥蒂",
        "深仇": "势不两立",
        "血仇": "不共戴天",
    }
    return tag_map.get(grudge_level, "")
