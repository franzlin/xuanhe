"""
《宣和二年》派系系统
对齐《核心机制》§7派系斗争机制
四大派系：蔡党/清流/西军/帝党
"""
import random

# 派系初始状态
FACTIONS = {
    "蔡党": {"influence": "强势", "treasury": 50000, "label": "蔡京集团", "desc": "以蔡京为首的权臣集团，掌控朝政"},
    "清流": {"influence": "疲弱", "treasury": 20000, "label": "士林清流", "desc": "以李纲、陈东为首的正直士大夫"},
    "西军": {"influence": "坚守", "treasury": 30000, "label": "西军集团", "desc": "以种师道为首的边防军方势力"},
    "帝党": {"influence": "中立", "treasury": 80000, "label": "皇帝近臣", "desc": "围绕宋徽宗的宫廷势力"},
}

# 派系关系（态度从-3到+3）
FACTION_RELATIONS = {
    ("蔡党","清流"): -3, ("蔡党","西军"): -2, ("蔡党","帝党"): 1,
    ("清流","蔡党"): -3, ("清流","西军"): 1, ("清流","帝党"): 0,
    ("西军","蔡党"): -2, ("西军","清流"): 1, ("西军","帝党"): 1,
    ("帝党","蔡党"): 1, ("帝党","清流"): 0, ("帝党","西军"): 1,
}


def get_faction_info():
    """获取派系状态信息"""
    info = {}
    for name, data in FACTIONS.items():
        info[name] = dict(data)
    return info


def get_faction_attitude(from_faction, to_faction):
    """获取派系间态度"""
    return FACTION_RELATIONS.get((from_faction, to_faction), 0)


def get_faction_alignment_effect(player_party):
    """获取派系倾向加成"""
    if not player_party or player_party not in FACTIONS:
        return {"power_bonus": 0, "money_bonus": 0, "prestige_bonus": 0}
    
    faction = FACTIONS.get(player_party, {})
    infl = faction.get("influence", "中立")
    bonus = {"极弱": -2, "疲弱": -1, "中立": 0, "坚守": 1, "强势": 2, "权倾": 3}
    ib = bonus.get(infl, 0)
    return {
        "power_bonus": ib,
        "money_bonus": faction.get("treasury", 0) // 10000,
        "prestige_bonus": max(0, ib),
    }


def month_faction_event(player_party, current_time):
    """月度派系事件"""
    if not player_party:
        return None
    
    events = {
        "蔡党": [
            "蔡党又在朝中安插亲信。",
            "蔡京府门前车马不绝，求官者络绎不绝。",
            "听闻蔡党正在打压某位不附己的言官。",
        ],
        "清流": [
            "太学生们在茶坊议论朝政，言辞激烈。",
            "李纲上书论边防之事，语重心长。",
            "清流士大夫聚于某寺院，以文会友。",
        ],
        "西军": [
            "西军将士在边境巡逻，马匹疲惫。",
            "种师道正在巡视边防营寨。",
            "有西军老卒在酒馆讲述边关往事。",
        ],
        "帝党": [
            "徽宗在艮岳赏玩奇石，不理朝政。",
            "宫中传出消息，某位宦官新得宠幸。",
            "帝心不悦，近日罢朝数次。",
        ],
    }
    
    party_events = events.get(player_party, [])
    if party_events:
        return random.choice(party_events)
    return None
