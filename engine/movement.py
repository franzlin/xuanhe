"""
《宣和二年》地理移动系统
对齐《核心机制》§四地图距离与移动机制
"""
# 移动方式表
MOVEMENT_TYPES = {
    "步行": {"speed": "30-40里/日", "cost_per_100li": 0.1, "energy_per_100li": 5},
    "骑马": {"speed": "60-80里/日", "cost_per_100li": 0.5, "energy_per_100li": 3},
    "马车": {"speed": "50-60里/日", "cost_per_100li": 0.8, "energy_per_100li": 2},
    "内河船": {"speed": "70-90里/日", "cost_per_100li": 0.6, "energy_per_100li": 1},
    "海船": {"speed": "120-150里/日", "cost_per_100li": 1.5, "energy_per_100li": 2},
}

# 地区遇匪概率
REGION_RISK = {
    "江南路": {"bandit": 0.15, "official": 0.40, "desc": "富庶之地，应奉局勒索"},
    "北方边境": {"bandit": 0.35, "official": 0.50, "desc": "辽金细作、逃兵"},
    "东南沿海": {"bandit": 0.20, "official": 0.30, "desc": "海盗、私盐贩"},
    "西北边陲": {"bandit": 0.40, "official": 0.15, "desc": "西夏游骑、野兽"},
    "中原腹地": {"bandit": 0.20, "official": 0.30, "desc": "梁山贼寇、流民"},
}

DEFAULT_DISTANCES = {
    ("汴京","杭州"): 2000,
    ("汴京","洛阳"): 400,
    ("汴京","大名府"): 500,
    ("汴京","江宁府"): 1200,
    ("杭州","泉州"): 800,
    ("汴京","太原"): 1000,
}

def calc_travel(origin, destination, method="步行", player_power="微末"):
    """计算旅行消耗"""
    import random
    dist = 0
    for (o, d), distance in DEFAULT_DISTANCES.items():
        if (o == origin and d == destination) or (o == destination and d == origin):
            dist = distance
            break
    if dist == 0:
        dist = random.randint(300, 1500)
    
    mt = MOVEMENT_TYPES.get(method, MOVEMENT_TYPES["步行"])
    speed_parts = mt["speed"].split("-")
    avg_speed = (int(speed_parts[0]) + int(speed_parts[1].replace("里/日",""))) // 2
    days = dist // avg_speed + (1 if dist % avg_speed > 0 else 0)
    
    hundred_li = dist / 100
    gold_cost = int(hundred_li * mt["cost_per_100li"] * 10) 
    energy_cost = int(hundred_li * mt["energy_per_100li"])
    
    return {
        "distance": dist,
        "days": days,
        "gold_cost": gold_cost,
        "energy_cost": energy_cost,
        "method": method,
        "avg_speed": avg_speed,
    }
