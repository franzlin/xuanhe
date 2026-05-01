"""
《宣和二年》随从/家仆系统 (Follower System)
对齐《核心机制》§三十二

设计原则：
- 四种随从类型各有独特功能
- 忠诚度受善待/亏待/危险任务影响
- 随从可成长（每年检定）也可能死亡/叛逃
- 权力值影响随从数量上限
"""
import random
import json


# ============================
# 随从类型与属性
# ============================

FOLLOWER_TYPES = {
    "仆役": {
        "描述": "帮办杂务、跑腿传信",
        "特长": "精力消耗-1（日常杂务自动处理）",
        "招募条件": {"权力值": "≥微末", "金钱": "2~5贯/月"},
        "战斗能力": "无",
        "获取方式": ["雇佣", "感恩"],
        "租金词": "月薪",
    },
    "护卫": {
        "描述": "随身护卫、抵挡袭击",
        "特长": "被暗杀/袭击时抵挡1次（护卫受伤/死亡）",
        "招募条件": {"权力值": "≥小吏", "金钱": "5~15贯/月"},
        "战斗能力": "可参与战斗",
        "获取方式": ["雇佣", "招揽", "感恩"],
        "租金词": "月饷",
    },
    "谋士": {
        "描述": "出谋划策、辅助判定",
        "特长": "智力+1级辅助（相关判定成功率↑）",
        "招募条件": {"权力值": "≥地方", "金钱": "10~30贯/月"},
        "战斗能力": "无（可提供战术建议）",
        "获取方式": ["招揽", "感恩"],
        "租金词": "束脩",
    },
    "商帮": {
        "描述": "协助经营、管理产业",
        "特长": "产业月收入+1档（限1处产业）",
        "招募条件": {"权力值": "≥小吏", "金钱": "3~10贯/月"},
        "战斗能力": "无",
        "获取方式": ["雇佣", "招揽"],
        "租金词": "工钱",
    },
}

# 忠诚度
LOYALTY_LEVELS = {
    "高": {"背叛概率": 0.02, "额外效果": "主动预警危险/告密"},
    "中": {"背叛概率": 0.10, "额外效果": "完成任务，但不会超额付出"},
    "低": {"背叛概率": 0.35, "额外效果": "可能叛逃/告密/偷窃"},
}

# 获取方式
ACQUISITION_METHODS = {
    "雇佣": {
        "条件": "权力值≥小吏+金钱",
        "随从品质": "普通",
        "金钱消耗": "按类型月薪",
        "初始忠诚": "中",
    },
    "感恩": {
        "条件": "帮助NPC解决困境（好感≥友善）",
        "随从品质": "良（忠心+特长）",
        "金钱消耗": 0,
        "初始忠诚": "高",
    },
    "招揽": {
        "条件": "魅力≥优良+人望≥小有名气",
        "随从品质": "优（有技能/武力）",
        "金钱消耗": "安家费5~30贯",
        "初始忠诚": "中",
    },
    "收养": {
        "条件": "无条件（孤儿/流浪者）",
        "随从品质": "随机（需培养）",
        "金钱消耗": "1~5贯/月抚养",
        "初始忠诚": "高",
    },
}


def get_follower_cap(player_power):
    """根据权力值获取随从上限"""
    power_caps = {
        "微末": 1,
        "小吏": 2,
        "地方": 3,
        "朝堂": 5,
        "权倾": 7,
    }
    return power_caps.get(player_power, 1)


def create_follower(name, f_type, method="雇佣"):
    """创建随从记录"""
    if f_type not in FOLLOWER_TYPES:
        return None

    info = FOLLOWER_TYPES[f_type]
    method_info = ACQUISITION_METHODS.get(method, ACQUISITION_METHODS["雇佣"])

    loyalty = method_info["初始忠诚"]
    skill = info.get("特长", "")

    return {
        "name": name,
        "f_type": f_type,
        "loyalty": loyalty,
        "skill": skill,
        "salary": 0,  # 实际月薪按类型和品质计算
        "months_served": 0,
        "is_alive": True,
        "growth_progress": 0,
    }


def use_follower_action(follower, action_type):
    """
    使用随从执行某项功能
    返回: (效果描述, 消耗, 成功率)
    """
    if not follower or not follower.get("is_alive"):
        return "随从不可用", 0, 0

    f_type = follower.get("f_type", "")
    loyalty = follower.get("loyalty", "中")

    # 忠诚低时拒绝服务概率
    if loyalty == "低" and random.random() < 0.2:
        return f"{follower['name']}推脱不从", 0, 0

    actions = {
        "跑腿传信": {
            "适用": ["仆役", "护卫", "商帮"],
            "消耗": {"精力": 1, "时间": "1日"},
            "效果": "远距离传递消息/物品，无需亲自前往",
            "成功率": 0.95,
        },
        "打探消息": {
            "适用": ["仆役", "谋士"],
            "消耗": {"精力": 2, "金钱": 1},
            "效果": "获取1条情报（品质=传闻~可信）",
            "成功率": 0.6 if loyalty == "高" else 0.45,
        },
        "护卫随行": {
            "适用": ["护卫"],
            "消耗": {"精力": 0},
            "效果": "被暗杀/袭击时护卫可抵挡1次（护卫受伤或死亡）",
            "成功率": 1.0,
        },
        "辅助经营": {
            "适用": ["商帮"],
            "消耗": {"精力": 0},
            "效果": "指定产业月收入+1档",
            "成功率": 0.85,
        },
        "协助判定": {
            "适用": ["谋士"],
            "消耗": {"精力": 0},
            "效果": "相关行动成功率+0.5级",
            "成功率": 0.9,
        },
    }

    if action_type not in actions:
        return "不支持此操作", 0, 0

    action = actions[action_type]
    if f_type not in action["适用"]:
        return f"{follower['name']}无法执行此任务", 0, 0

    success = random.random() < action["成功率"]
    if success:
        return action["效果"], action["消耗"].get("精力", 0), action["成功率"]
    else:
        failure_msgs = {
            "打探消息": "消息打探失败，一无所获",
            "跑腿传信": "传信途中遇到意外，消息未送达",
            "辅助经营": "经营失误，本月无额外收益",
        }
        return failure_msgs.get(action_type, "行动失败"), action["消耗"].get("精力", 0), action["成功率"]


def check_loyalty_change(follower, player_action_type, is_dangerous=False):
    """
    检查忠诚度变化
    player_action_type: "善待"/"亏待"/"危险任务"
    """
    if player_action_type == "善待":
        # 赏赐、加薪、关怀
        if follower["loyalty"] == "低":
            follower["loyalty"] = "中"
            return f"{follower['name']}感激涕零，忠诚度提升至'中'"
        elif follower["loyalty"] == "中" and random.random() < 0.3:
            follower["loyalty"] = "高"
            return f"{follower['name']}忠心耿耿，忠诚度提升至'高'"

    elif player_action_type == "亏待":
        if follower["loyalty"] == "高":
            follower["loyalty"] = "中"
            return f"{follower['name']}心寒齿冷，忠诚度降至'中'"
        elif follower["loyalty"] == "中" and random.random() < 0.5:
            follower["loyalty"] = "低"
            return f"{follower['name']}心生去意，忠诚度降至'低'"

    elif is_dangerous:
        if follower["loyalty"] in ("中", "低") and random.random() < 0.4:
            follower["loyalty"] = "低"
            return f"危险任务让{follower['name']}心生畏惧"

    return None


def check_follower_death_or_betray(follower):
    """每月检查：随从是否死亡/叛逃"""
    if not follower.get("is_alive"):
        return None

    loyalty = follower.get("loyalty", "中")
    f_type = follower.get("f_type", "")

    # 忠诚低时叛逃概率
    betray_prob = LOYALTY_LEVELS.get(loyalty, {"背叛概率": 0.1})["背叛概率"]
    if random.random() < betray_prob:
        follower["is_alive"] = False
        stolen = random.randint(1, 20) if f_type != "仆役" else 0
        return f"{follower['name']}叛逃！" + (f"卷走{stolen}贯财物！" if stolen > 0 else "")

    # 护卫在战斗中死亡（仅在触发战斗时检查，此处为常规月检）
    if f_type == "护卫" and random.random() < 0.02:
        follower["is_alive"] = False
        return f"{follower['name']}在一次冲突中重伤不治"

    return None


def grow_follower(follower):
    """随从成长检定（每年1次）"""
    follower["months_served"] = follower.get("months_served", 0) + 1

    # 每年（12个月）检定一次
    if follower["months_served"] >= 12 and follower["loyalty"] == "高":
        follower["months_served"] = 0
        follower["growth_progress"] = follower.get("growth_progress", 0) + 1

        if follower["growth_progress"] >= 3:
            # 特长升级
            old_skill = follower.get("skill", "")
            follower["skill"] = f"{old_skill}（精进）"
            return f"{follower['name']}随侍多年，技艺精进！"

    return None
