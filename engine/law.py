"""
《宣和二年》法律系统
对齐《核心机制》§12 + 《基本文件1》§四《宋刑统》
"""
import random

# 罪名表（对齐基本文件1§四）
CRIMES = {
    "谋反": {"type":"重罪","penalty":"凌迟处死，亲属缘坐","bribe_threshold":100},
    "杀人": {"type":"重罪","penalty":"斩","bribe_threshold":80},
    "强盗": {"type":"重罪","penalty":"斩","bribe_threshold":70},
    "贪污": {"type":"重罪","penalty":"绞或斩","bribe_threshold":50},
    "受贿枉法": {"type":"重罪","penalty":"绞","bribe_threshold":40},
    "伪造交子": {"type":"重罪","penalty":"斩","bribe_threshold":60},
    "私盐持械": {"type":"重罪","penalty":"斩","bribe_threshold":50},
    "通敌": {"type":"重罪","penalty":"斩","bribe_threshold":100},
    "窃盗": {"type":"轻罪","penalty":"笞/杖/徒/流/刺配","bribe_threshold":20},
    "斗殴": {"type":"轻罪","penalty":"笞/杖","bribe_threshold":15},
    "恐吓取财": {"type":"轻罪","penalty":"准窃盗加等","bribe_threshold":20},
    "犯奸": {"type":"轻罪","penalty":"徒二年","bribe_threshold":25},
    "赌博": {"type":"轻罪","penalty":"杖","bribe_threshold":10},
    "违令": {"type":"轻罪","penalty":"笞或杖","bribe_threshold":5},
}

# 判决影响因子
JUDGE_FACTORS = {
    "offi_greed": {"低":0.5, "中":1.0, "高":1.5},     # 官员贪欲
    "party_intervention": {"无":0, "蔡党":0.8, "清流":-0.3, "西军":-0.2, "帝党":0.5}, # 派系干预
    "power_effect": {"微末":1.0, "小吏":0.8, "地方":0.6, "朝堂":0.3, "权倾":0.1}, # 权力压制
}


def judge(player, crime_name, player_party=""):
    """
    法律审判流程
    返回判决结果
    """
    crime = CRIMES.get(crime_name, CRIMES["违令"])
    greed = player.get('greed', '中')
    power = player.get('power', '微末')
    
    # 基础判决
    base_severity = 1.0 if crime["type"] == "重罪" else 0.5
    
    # 官员贪欲：影响收贿可能性
    greed_factor = JUDGE_FACTORS["offi_greed"].get(greed, 1.0)
    
    # 权力值影响：权力越高越容易脱罪
    power_factor = JUDGE_FACTORS["power_effect"].get(power, 1.0)
    
    # 派系干预
    party_factor = JUDGE_FACTORS["party_intervention"].get(player_party, 0)
    
    # 行贿判定
    can_bribe = crime["bribe_threshold"] <= 50 or greed_factor >= 1.0
    bribe_works = False
    if can_bribe:
        bribe_chance = 0.6 - power_factor * 0.3
        bribe_works = random.random() < bribe_chance
    
    # 最终判决
    if bribe_works:
        verdict = "行贿成功，从轻发落"
        effective_penalty = "罚铜 + 笞刑（折杖释放）" if power_factor < 0.6 else "无罪释放"
    elif power_factor < 0.3:
        verdict = "权力压制，无人敢问"
        effective_penalty = "不予追究"
    elif party_factor > 0.5:
        verdict = "派系干预，大事化小"
        effective_penalty = "降职/罚俸"
    else:
        verdict = "依法判决"
        effective_penalty = crime["penalty"]
    
    return {
        "crime": crime_name,
        "type": crime["type"],
        "verdict": verdict,
        "penalty": effective_penalty,
        "base_penalty": crime["penalty"],
        "bribe_possible": can_bribe,
        "bribe_used": bribe_works,
        "greed": greed,
        "power": power,
    }
