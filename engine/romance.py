"""
《宣和二年》风月/后宫系统
对齐《核心机制》风月/后宫相关章节
"""
import random

# 风月场所
PLEASURE_VENUES = {
    "樊楼": {"desc":"汴京第一酒楼，名妓云集", "cost":(5,20), "risk":0.2},
    "勾栏行院": {"desc":"瓦舍中的风月场所", "cost":(2,10), "risk":0.3},
    "茶坊": {"desc":"清雅茶肆，可听曲谈心", "cost":(1,5), "risk":0.1},
}

# 后宫位份
HAREM_RANKS = [
    "采女", "宝林", "御女", "才人", "美人", "婕妤",
    "嫔", "昭仪", "妃", "贵妃", "皇贵妃", "皇后"
]


def visit_pleasure(player, venue_name="樊楼", purpose="打茶围"):
    """
    风月行动
    返回：{花销, 情报获取, 人脉变化, 风险事件}
    """
    venue = PLEASURE_VENUES.get(venue_name, PLEASURE_VENUES["樊楼"])
    cost = random.randint(*venue["cost"])
    
    # 魅力影响
    charm = player.get('charm', '普通')
    charm_bonus = {"拙劣": -2, "平庸": -1, "普通": 0, "优良": 1, "卓越": 2}.get(charm, 0)
    
    # 情报获取
    intel_gain = random.randint(0, 2) + max(0, charm_bonus)
    
    # 人脉变化
    bond_change = random.randint(-1, 1) + charm_bonus
    
    # 风险判定
    risk_roll = random.random()
    risk_event = None
    if risk_roll < venue["risk"]:
        risks = [
            "被老鸨讹诈，多花了5贯",
            "被官差盘问，惹了麻烦",
            "染了暗疾，身体微恙",
            "官声受损，被同僚风言风语",
        ]
        risk_event = random.choice(risks)
        if "官声" in risk_event:
            bond_change -= 1
        if "多花" in risk_event:
            cost += 5
    
    # 减压效果
    stress_relief = random.randint(1, 3)
    
    result = {
        "venue": venue_name,
        "cost": cost,
        "intel_gain": intel_gain,
        "bond_change": bond_change,
        "stress_relief": stress_relief,
        "risk_event": risk_event,
        "description": f"于{venue_name}{purpose}，花费{cost}贯"
    }
    if intel_gain > 0:
        result["description"] += f"，打听到一些消息"
    if risk_event:
        result["description"] += f"。{risk_event}"
    
    return result


def harem_action(player, action_type, current_rank_index=0):
    """
    后宫行动（妃嫔专属）
    """
    rank = HAREM_RANKS[current_rank_index] if current_rank_index < len(HAREM_RANKS) else "采女"
    
    actions = {
        "妆扮候驾": {"energy":4, "charm_req":0, "desc":"精心妆扮，等待皇帝临幸"},
        "圣前献艺": {"energy":5, "charm_req":1, "desc":"展示才艺以博君心"},
        "探望皇后": {"energy":3, "charm_req":0, "desc":"向皇后请安，联络感情"},
        "结交宫人": {"energy":3, "charm_req":0, "desc":"赏赐宫人黄门，打通关节"},
        "焚香修道": {"energy":2, "charm_req":0, "desc":"清心寡欲，明哲保身"},
    }
    
    act = actions.get(action_type, actions["妆扮候驾"])
    
    # 宠幸判定
    charm = player.get('charm', '普通')
    charm_ok = {"拙劣":0, "平庸":1, "普通":2, "优良":3, "卓越":4}.get(charm, 1) >= act["charm_req"]
    
    favor_gain = 0
    if action_type == "圣前献艺":
        favor_gain = random.randint(1, 5)
    elif action_type == "妆扮候驾":
        favor_gain = random.randint(0, 3)
    elif action_type == "探望皇后":
        favor_gain = random.randint(0, 2)
    else:
        favor_gain = random.randint(0, 1)
    
    result = {
        "action": act["desc"],
        "favor_gain": favor_gain,
        "energy_cost": act["energy"],
        "current_rank": rank,
        "success": charm_ok,
        "description": f"后宫之中，{act['desc']}。"
    }
    if favor_gain >= 3:
        result["description"] += "龙颜大悦！"
        result["rank_up"] = current_rank_index < len(HAREM_RANKS) - 1
    else:
        result["description"] += "一切如常。"
        result["rank_up"] = False
    
    return result
