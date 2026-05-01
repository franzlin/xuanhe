"""
《宣和二年》物品/道具系统 (Item System)
对齐《核心机制》§三十一

设计原则：
- 六类物品各有不同获取方式和使用效果
- 赠礼匹配身份→好感修正
- 装备品质修正战斗判定
- 证据/文书影响构陷和翻案
- 毒药需百工技能配制，下毒需阴毒属性
- 物品有保管风险（被搜/被盗/被伪造）
"""
import random
import json


# ============================
# 物品分类
# ============================

ITEM_CATEGORIES = {
    "礼物": {
        "示例": ["珠玉首饰", "华服锦缎", "名家书画", "名茶贡品", "西域香料"],
        "获取方式": ["购买", "战利品", "馈赠"],
        "核心属性": "价值（匹配对方身份→好感修正）",
    },
    "装备": {
        "示例": ["宝刀", "铁甲", "良弓", "骏马"],
        "获取方式": ["购买", "赏赐", "缴获"],
        "核心属性": "品质（五级，修正战斗/武力判定）",
    },
    "文书": {
        "示例": ["密信", "官文", "契约", "邸报"],
        "获取方式": ["交互获取", "搜查", "伪造"],
        "核心属性": "证据效力+时效+持有风险",
    },
    "证据": {
        "示例": ["通奸物证", "贪腐账本", "反诗原件", "密谋记录"],
        "获取方式": ["搜查", "暗桩提供", "购买"],
        "核心属性": "证据强度（决定构陷/翻案成功率）",
    },
    "毒药/药物": {
        "示例": ["砒霜", "蒙汗药", "金疮药", "续命丹"],
        "获取方式": ["配制（需百工/医术）", "黑市购买"],
        "核心属性": "效果强度+被检出概率",
    },
    "特殊道具": {
        "示例": ["兵符", "印信", "敕令", "虎皮"],
        "获取方式": ["剧情获得", "赏赐"],
        "核心属性": "解锁特定交互/指令",
    },
}

# 装备品质（五级）
EQUIPMENT_QUALITY = {
    "粗劣": {"战斗修正": -1, "价值": "1~5贯", "描述": "市井粗制"},
    "寻常": {"战斗修正": 0, "价值": "5~20贯", "描述": "军中制式"},
    "精良": {"战斗修正": +1, "价值": "20~100贯", "描述": "名匠所制"},
    "优异": {"战斗修正": +2, "价值": "100~500贯", "描述": "传家之宝"},
    "神兵": {"战斗修正": +3, "价值": "500贯以上", "描述": "千古名器"},
}

# 物品价格参考（宋代物价）
ITEM_PRICES = {
    "珠玉首饰": (5, 50),
    "华服锦缎": (3, 30),
    "名家书画": (10, 200),
    "名茶贡品": (2, 15),
    "西域香料": (5, 40),
    "宝刀": (15, 80),
    "铁甲": (10, 60),
    "良弓": (8, 30),
    "骏马": (30, 200),
    "砒霜": (5, 20),
    "蒙汗药": (3, 10),
    "金疮药": (1, 5),
    "续命丹": (20, 100),
    "密信": (1, 5),
    "官文": (5, 50),
    "契约": (2, 10),
}

# 赠礼效果（按价值和身份匹配度）
GIFT_EFFECT = {
    "极不匹配": {"好感变化": -3, "描述": "此物粗鄙，是在羞辱我吗？"},
    "不匹配": {"好感变化": 0, "描述": "收下礼物，但未显欢喜"},
    "尚可": {"好感变化": +2, "描述": "礼物得体，颇为受用"},
    "匹配": {"好感变化": +4, "描述": "大喜过望，连连称赞"},
    "极佳": {"好感变化": +6, "描述": "此物正合心意，视若珍宝"},
}


def get_item_price(item_name):
    """获取物品价格范围"""
    return ITEM_PRICES.get(item_name, (1, 10))


def evaluate_gift_match(item_category, item_value, npc_identity, npc_power, npc_greed="中"):
    """
    评估礼物匹配度
    返回: (匹配等级, 好感变化值)
    """
    # 基础匹配度
    base_score = 0

    # 礼物价值相对于NPC身份
    if item_value < 3:
        base_score = -1
    elif item_value < 10:
        base_score = 0
    elif item_value < 30:
        base_score = 1
    else:
        base_score = 2

    # 贪欲高的NPC更容易被金钱打动
    if npc_greed == "高":
        base_score += 1

    # 映射到匹配等级
    if base_score <= -1:
        match_level = "极不匹配"
    elif base_score == 0:
        match_level = "不匹配"
    elif base_score == 1:
        match_level = "尚可"
    elif base_score == 2:
        match_level = "匹配"
    else:
        match_level = "极佳"

    effect = GIFT_EFFECT[match_level]
    return match_level, effect["好感变化"], effect["描述"]


def apply_equipment_bonus(quality, player_military_order):
    """装备品质修正战斗"""
    if quality not in EQUIPMENT_QUALITY:
        return 0
    return EQUIPMENT_QUALITY[quality]["战斗修正"]


def use_evidence(evidence_strength):
    """
    证据用于构陷/翻案
    返回: 成功率修正级数
    """
    strength_map = {
        "微弱": +1,
        "一般": +1,
        "有力": +2,
        "铁证": +3,
    }
    return strength_map.get(evidence_strength, 0)


def use_poison(poison_type, player_baigong_level, player_yindu_level="低"):
    """
    毒药使用判定
    返回: (是否成功, 被检出概率, 效果描述)
    """
    poison_data = {
        "砒霜": {
            "配制难度": "登堂入室",
            "效果": "致死",
            "检出概率": 0.4,
        },
        "蒙汗药": {
            "配制难度": "初窥门径",
            "效果": "昏迷",
            "检出概率": 0.2,
        },
        "慢性毒": {
            "配制难度": "融会贯通",
            "效果": "渐进虚弱→死亡",
            "检出概率": 0.15,
        },
    }

    if poison_type not in poison_data:
        return False, 0, "未知毒药"

    data = poison_data[poison_type]
    skill_order = ["未涉猎", "略知一二", "初窥门径", "登堂入室", "融会贯通", "出神入化"]

    # 检查技能门槛
    try:
        player_idx = skill_order.index(player_baigong_level)
        required_idx = skill_order.index(data["配制难度"])
    except ValueError:
        return False, data["检出概率"], f"技能不足，无法配制{poison_type}"

    if player_idx < required_idx:
        return False, data["检出概率"] * 1.5, f"技能不足，{poison_type}配制失败"

    # 下毒需要阴毒属性
    if player_yindu_level == "低":
        return True, data["检出概率"] * 1.3, "虽能配制，但缺乏下毒的胆魄和手法"

    return True, data["检出概率"], f"成功使用{poison_type}"


def check_item_risk(item, player_location="东京开封府"):
    """
    检查物品保管风险
    返回: (风险类型, 触发概率, 后果)
    """
    risks = []

    # 违禁品风险
    forbidden_items = ["砒霜", "反诗原件", "伪证", "兵符_非授权"]
    if item.get("name") in forbidden_items or item.get("tags") and "违禁" in str(item.get("tags")):
        risks.append({
            "风险类型": "被搜查",
            "触发条件": "被捕/抄家/皇城司突击检查",
            "后果": "违禁品被发现→定罪证据",
        })

    # 贵重品被盗风险
    if item.get("category") in ("礼物", "装备") and item.get("value", 0) > 50:
        risks.append({
            "风险类型": "被盗",
            "触发条件": "住宅治安低+家仆好感低",
            "后果": "贵重物品丢失",
        })

    # 文书被伪造风险
    if item.get("category") in ("文书", "证据"):
        risks.append({
            "风险类型": "被伪造",
            "触发条件": "对方智力≥优良+百工≥初窥门径",
            "后果": "你的文书/证据被伪造出反证",
        })

    return risks


def create_item(category, name, detail="", quality="寻常"):
    """创建物品记录"""
    return {
        "category": category,
        "name": name,
        "tags": "[]",
        "status": "正常",
        "detail": detail,
        "quality": quality if category == "装备" else "",
        "expire_month": "",
        "acquired_month": "",
        "is_key": False,  # 关键物品不受10条上限约束
    }
