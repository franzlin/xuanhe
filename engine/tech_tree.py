"""
《宣和二年》科技研发系统
对齐《核心机制》§16 + 《基本文件2》第一部分科技树
研发流程：立项→试制→推广（三阶段）
"""
from .db import get_tech_research, init_tech_research, update_tech_research

# ============================================================
# 科技树定义（对齐《基本文件2》可研发方向）
# ============================================================

TECH_TREE = {
    "军事火器": [
        {"name": "管形火器", "cost": 60, "prerequisites": [], "category":"军事火器",
         "effects": {"military_power": 2}, "skill":"百工",
         "desc": "竹木筒发射弹丸的突火枪，近战破甲。火药配比：硝硫炭。"},
        {"name": "铁火炮", "cost": 80, "prerequisites": ["管形火器"], "category":"军事火器",
         "effects": {"military_power": 3, "troops_cap": 10}, "skill":"百工",
         "desc": "铸铁外壳火药弹（震天雷），破片杀伤。攻城利器。"},
        {"name": "火药提纯", "cost": 70, "prerequisites": ["管形火器"], "category":"军事火器",
         "effects": {"military_power": 2}, "skill":"百工",
         "desc": "硝石重结晶提纯，燃烧更充分，哑火率大幅降低。"},
        {"name": "配重抛石机", "cost": 90, "prerequisites": ["火药提纯"], "category":"军事火器",
         "effects": {"military_power": 3, "troops_cap": 20}, "skill":"百工",
         "desc": "回回炮雏形，射程精度远超人力拽炮。攻城拔寨之重器。"},
        {"name": "火器上舰", "cost": 100, "prerequisites": ["铁火炮", "配重抛石机"], "category":"军事火器",
         "effects": {"military_power": 5, "troops_cap": 30}, "skill":"兵学",
         "desc": "解决防潮后坐力后装备战船，水战优势极大提升。"},
    ],
    "农业水利": [
        {"name": "稻麦复种", "cost": 50, "prerequisites": [], "category":"农业水利",
         "effects": {"money_income": 3, "health": "趋升"}, "skill":"水利",
         "desc": "江南冬季种麦，一年两熟。耕地利用率倍增。"},
        {"name": "桑基鱼塘", "cost": 60, "prerequisites": ["稻麦复种"], "category":"农业水利",
         "effects": {"money_income": 5}, "skill":"水利",
         "desc": "塘基植桑、塘内养鱼的生态循环农业。经济效益与生态兼备。"},
        {"name": "大型水利", "cost": 100, "prerequisites": ["桑基鱼塘"], "category":"农业水利",
         "effects": {"money_income": 8, "health":"趋升", "prestige_civilian": 2}, "skill":"水利",
         "desc": "钱塘江海塘、太湖泄水闸等大型工程。旱涝保收，万民受益。"},
        {"name": "良种选育", "cost":  60, "prerequisites": ["稻麦复种"], "category":"农业水利",
         "effects": {"money_income": 4, "health":"趋升"}, "skill":"水利",
         "desc": "选育抗逆高产稻麦品种。长期增产稳产的基础。"},
    ],
    "手工业制造": [
        {"name": "棉纺织推广", "cost": 50, "prerequisites": [], "category":"手工业制造",
         "effects": {"money_income": 4, "prestige_wealth": 1}, "skill":"商道",
         "desc": "搅车椎弓纺车改良，棉纺织业兴起。衣被天下。"},
        {"name": "煤焦化冶铁", "cost": 70, "prerequisites": [], "category":"手工业制造",
         "effects": {"military_power": 2, "money_income": 2}, "skill":"百工",
         "desc": "煤制焦炭提高炉温，铁器品质大增。军械民用俱益。"},
        {"name": "精密铸造", "cost": 80, "prerequisites": ["煤焦化冶铁"], "category":"手工业制造",
         "effects": {"military_power": 2, "money_income": 3, "prestige_literary": 1}, "skill":"百工",
         "desc": "失蜡法大型化，可铸天文仪器、重炮、精甲。"},
        {"name": "动力机械", "cost": 90, "prerequisites": ["精密铸造"], "category":"手工业制造",
         "effects": {"money_income": 6}, "skill":"百工",
         "desc": "水力风力驱动作坊。纺织、锻打、碾磨机械化萌芽。"},
    ],
    "科学与医学": [
        {"name": "历法改革", "cost": 50, "prerequisites": [], "category":"科学与医学",
         "effects": {"prestige_literary": 2, "money_income": 1}, "skill":"经义",
         "desc": "推行《统天历》（回归年365.2425日），精准授时利农桑。"},
        {"name": "人痘接种", "cost": 70, "prerequisites": [], "category":"科学与医学",
         "effects": {"health":"趋升", "prestige_civilian": 2, "energy_cap": 2}, "skill":"医术",
         "desc": "免疫学先驱。瘟疫事件死亡率大幅降低，民望官声同升。"},
        {"name": "天元术", "cost": 60, "prerequisites": ["历法改革"], "category":"科学与医学",
         "effects": {"prestige_literary": 2}, "skill":"经义",
         "desc": "代数符号化（秦九韶《数书九章》），数学水平跃升。"},
        {"name": "指南针海图", "cost": 80, "prerequisites": ["天元术"], "category":"科学与医学",
         "effects": {"money_income": 5, "troops_cap": 10}, "skill":"商道",
         "desc": "指南针配精细海图，远洋航行安全大幅提升。海贸扩展。"},
    ],
}

# 研发三阶段（对齐《核心机制》§16）
RESEARCH_PHASES = [
    {"phase": "立项", "cost_factor": 0.3, "skill_req": "略知一二", "desc": "投入资源论证可行性"},
    {"phase": "试制", "cost_factor": 0.4, "skill_req": "初窥门径", "desc": "匠人学者试验制造"},
    {"phase": "推广", "cost_factor": 0.3, "skill_req": "登堂入室", "desc": "行政推广规模化"},
]


def get_tech_tree():
    return TECH_TREE


def get_tech_status(user_id):
    """获取科技研发状态（对齐三阶段机制）"""
    db_techs = get_tech_research(user_id)
    db_map = {t['tech_name']: t for t in db_techs}

    result = {}
    for category, techs in TECH_TREE.items():
        result[category] = []
        for tech in techs:
            db_record = db_map.get(tech['name'], {})
            tech_status = {
                "name": tech['name'],
                "category": category,
                "cost": tech['cost'],
                "prerequisites": tech['prerequisites'],
                "effects": tech['effects'],
                "skill": tech.get('skill', ''),
                "desc": tech['desc'],
                "status": db_record.get('status', 'locked'),
                "research_points": db_record.get('research_points', 0),
                "total_points_required": db_record.get('total_points_required', tech['cost']),
            }
            # 前置条件
            prereqs_met = all(
                db_map.get(pre, {}).get('status') == 'researched'
                for pre in tech['prerequisites']
            )
            tech_status['prereqs_met'] = prereqs_met
            tech_status['can_research'] = tech_status['status'] != 'researched' and prereqs_met
            result[category].append(tech_status)

    total = sum(len(v) for v in TECH_TREE.values())
    researched = sum(1 for t in db_map.values() if t.get('status') == 'researched')
    result['_summary'] = {"total": total, "researched": researched}
    return result


def can_research_tech(user_id, tech_name):
    status = get_tech_status(user_id)
    for cat_list in status.values():
        if isinstance(cat_list, list):
            for t in cat_list:
                if t['name'] == tech_name:
                    return t.get('can_research', False)
    return False


def research_tech(user_id, tech_name, research_points=0):
    """研发科技（三阶段：立项→试制→推广）"""
    db_techs = get_tech_research(user_id)
    db_map = {t['tech_name']: t for t in db_techs}

    if tech_name not in db_map:
        return {"error": f"科技不存在：{tech_name}"}

    record = db_map[tech_name]
    if record['status'] == 'researched':
        return {"error": "该科技已完成研发"}

    tech_def = None
    for cat, techs in TECH_TREE.items():
        for t in techs:
            if t['name'] == tech_name:
                tech_def = t
                break
        if tech_def: break

    if not tech_def:
        return {"error": "科技定义未找到"}

    for pre in tech_def['prerequisites']:
        pre_record = db_map.get(pre, {})
        if pre_record.get('status') != 'researched':
            return {"error": f"前置科技未完成：{pre}"}

    current_points = record.get('research_points', 0)
    total_required = record.get('total_points_required', tech_def['cost'])
    new_points = current_points + research_points

    if new_points >= total_required:
        update_tech_research(user_id, tech_name, {
            "status": "researched",
            "research_points": total_required,
        })
        return {"success":True, "completed":True, "tech":tech_name, "effects":tech_def['effects']}
    else:
        update_tech_research(user_id, tech_name, {
            "status": "researching",
            "research_points": new_points,
        })
        return {"success":True, "completed":False, "tech":tech_name, "progress":f"{new_points}/{total_required}"}


def get_research_bonus(user_id):
    """获取已研发科技的汇总加成"""
    db_techs = get_tech_research(user_id)
    researched = [t['tech_name'] for t in db_techs if t['status'] == 'researched']

    bonuses = {
        "money_income": 0, "military_power": 0, "troops_cap": 0,
        "energy_cap": 0, "prestige_civilian": 0, "prestige_literary": 0,
        "prestige_wealth": 0, "health_trend": None,
    }

    for cat, techs in TECH_TREE.items():
        for tech in techs:
            if tech['name'] in researched:
                for k, v in tech['effects'].items():
                    if k == "health" and v == "趋升":
                        bonuses["health_trend"] = "趋升"
                    elif k in bonuses:
                        bonuses[k] += v
    return bonuses


def init_tech_for_player(user_id):
    """为新角色初始化科技树"""
    all_techs = []
    for category, techs in TECH_TREE.items():
        for tech in techs:
            all_techs.append({"name": tech['name'], "category": category, "cost": tech['cost']})
    init_tech_research(user_id, all_techs)
