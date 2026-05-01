"""
《宣和二年》经营系统
对齐《核心机制》§10经营机制
"""
import random

# 产业类型
INDUSTRIES = {
    "商铺": {"cost": 50, "income_range": (3, 12), "skill": "商道", "risk": "市场波动"},
    "田庄": {"cost": 80, "income_range": (2, 8), "skill": "水利", "risk": "天灾"},
    "作坊": {"cost": 60, "income_range": (5, 15), "skill": "百工", "risk": "原料短缺"},
    "行商": {"cost": 40, "income_range": (1, 20), "skill": "商道", "risk": "盗匪"},
}

PI = {"拙劣": -2, "平庸": -1, "普通": 0, "优良": 1, "卓越": 2}

def calc_business_income(player, industry_type, investment="一般"):
    """计算单次经营收入"""
    ind = INDUSTRIES.get(industry_type, INDUSTRIES["商铺"])
    base = random.randint(*ind["income_range"])
    
    # 智力/魅力加成
    intel_bonus = PI.get(player.get('intelligence', '普通'), 0)
    charm_bonus = PI.get(player.get('charm', '普通'), 0)
    
    # 技能加成
    skills = player.get('skills', {})
    if isinstance(skills, str):
        import json; skills = json.loads(skills)
    skill_level = skills.get(ind["skill"], '未涉猎')
    skill_bonus = {"未涉猎": 0, "略知一二": 1, "初窥门径": 2, "登堂入室": 3, "融会贯通": 4}.get(skill_level, 0)
    
    # 投资修正
    inv_bonus = {"一般": 0, "加大": 2, "全力": 5}
    
    income = base + intel_bonus + charm_bonus + (skill_bonus // 2) + inv_bonus.get(investment, 0)
    
    # 风险判定
    risk_roll = random.randint(1, 10)
    risk_event = None
    if risk_roll <= 2:
        risk_event = f"{ind['risk']}，收益受损"
        income = max(0, income - random.randint(3, 8))
    elif risk_roll >= 9:
        risk_event = "运气不错，收益略增"
        income += random.randint(2, 5)
    
    return {"income": max(0, income), "risk": risk_event, "base": base}
