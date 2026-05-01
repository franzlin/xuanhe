"""
《宣和二年》战斗六阶段系统
对齐《核心机制》§五战斗机制
流程：情报→准备(阵型)→远程→近战→士气→战后结算
"""
import random

# 阵型克制表
FORMATION_BONUS = {
    "锋矢": {"label": "锋矢阵", "target": "鹤翼", "effect": "突击+1"},
    "鹤翼": {"label": "鹤翼阵", "target": "方圆", "effect": "包围+1"},
    "方圆": {"label": "方圆阵", "target": "锋矢", "effect": "防御+1"},
}

FORMATION_ORDER = ["锋矢", "鹤翼", "方圆"]


def _get_attr_bonus(player, attr_name):
    """属性档位转数值加成"""
    val = player.get(attr_name, '普通')
    bonus = {"拙劣": -2, "平庸": -1, "普通": 0, "优良": 1, "卓越": 2}
    return bonus.get(val, 0)


def _get_skill_bonus(player, skill_name):
    """技能档位转数值加成"""
    skills = player.get('skills', {})
    if isinstance(skills, str):
        import json
        skills = json.loads(skills)
    val = skills.get(skill_name, '未涉猎')
    bonus = {"未涉猎": 0, "略知一二": 1, "初窥门径": 2, "登堂入室": 3, "融会贯通": 4}
    return bonus.get(val, 0)


def combat_resolve(player, opponent_name="敌军", opponent_strength="普通"):
    """
    完整战斗六阶段
    返回：{
        "result": "大胜"/"胜"/"僵持"/"败"/"惨败",
        "success": bool,
        "level": "惨败".."大胜",
        "casualties": int,
        "loot_money": int,
        "detail": "战果描述",
        "morale_boost": int,
        "formation_used": str,
        "phases": [阶段描述列表]
    }
    """
    phases = []

    # === 阶段1: 情报与侦察 ===
    intel_bonus = _get_attr_bonus(player, 'intelligence') + _get_skill_bonus(player, '兵学')
    intel_roll = random.randint(1, 10) + intel_bonus
    has_intel = intel_roll >= 7
    phases.append(f"情报侦察({'成功' if has_intel else '失败'}, 骰值{intel_roll})")

    # === 阶段2: 战前准备（阵型选择）===
    mil_bonus = _get_attr_bonus(player, 'military')
    player_formation = "锋矢"
    if mil_bonus >= 0:
        player_formation = random.choice(FORMATION_ORDER)
    
    # 敌阵型
    enemy_formation = random.choice(FORMATION_ORDER)
    
    # 阵型克制判定
    formation_advantage = 0
    for f_name, f_info in FORMATION_BONUS.items():
        if f_name == player_formation and f_info['target'] == enemy_formation:
            formation_advantage = 1
            phases.append(f"阵型克制：{f_info['label']}克{enemy_formation}阵，{f_info['effect']}")
            break
    if formation_advantage == 0:
        phases.append(f"阵型选用{player_formation}阵对敌{enemy_formation}阵，无克制关系")

    # === 阶段3: 远程阶段 ===
    mil_skill = _get_skill_bonus(player, '兵学')
    range_roll = random.randint(1, 10) + (mil_skill // 2)
    range_hit = range_roll >= 5
    phases.append(f"远程攻击{'命中' if range_hit else '未中'}(骰值{range_roll})")

    # === 阶段4: 近战阶段 ===
    base = player.get('troops', 10) if player.get('troops', 0) > 0 else 10
    combat_power = base + _get_attr_bonus(player, 'military') * 5 + formation_advantage * 3
    if has_intel:
        combat_power += 2
    if range_hit:
        combat_power += 2

    enemy_power = 10 + {"弱": -3, "普通": 0, "强": 3, "精锐": 6}.get(opponent_strength, 0)
    power_diff = combat_power - enemy_power + random.randint(-3, 3)

    # 结果判定
    if power_diff >= 8:
        result, success, casualties, loot = "大胜", True, random.randint(1, 5), random.randint(5, 30)
    elif power_diff >= 3:
        result, success, casualties, loot = "胜", True, random.randint(3, 8), random.randint(2, 15)
    elif power_diff >= -2:
        result, success, casualties, loot = "僵持", False, random.randint(5, 12), 0
    elif power_diff >= -7:
        result, success, casualties, loot = "败", False, random.randint(8, 20), -random.randint(3, 10)
    else:
        result, success, casualties, loot = "惨败", False, random.randint(15, 30), -random.randint(5, 20)

    phases.append(f"近战交锋：{result}(战力差{power_diff})")

    # === 阶段5: 士气判定 ===
    morale = 50 + mil_bonus * 10 + (5 if success else -10)
    if casualties > 15:
        morale -= 15
    morale = max(10, min(100, morale))
    morale_stable = morale >= 30
    phases.append(f"士气检定：{morale}/100，{'稳定' if morale_stable else '动摇'}")

    # === 阶段6: 战后结算 ===
    troop_loss = max(0, min(player.get('troops', 10), casualties))
    phases.append(f"战后结算：伤亡{casualties}人，缴获{abs(loot)}贯")

    # 声望变化
    prestige_map = {"大胜": 3, "胜": 1, "僵持": 0, "败": -1, "惨败": -2}
    prestige_change = prestige_map.get(result, 0)

    return {
        "result": result,
        "success": success,
        "level": result,
        "casualties": casualties,
        "loot_money": loot,
        "troop_loss": troop_loss,
        "detail": f"战果：{result}，伤亡{casualties}人，缴获{abs(loot)}贯",
        "morale_boost": morale,
        "formation_used": player_formation,
        "phases": phases,
        "prestige_change": prestige_change,
    }


def simple_combat(player, opponent_name, opponent_strength="普通"):
    """简化战斗（给process_action用，返回兼容旧格式）"""
    return combat_resolve(player, opponent_name, opponent_strength)
