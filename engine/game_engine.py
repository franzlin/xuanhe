"""
《宣和二年》游戏引擎 - 核心计算模块
包含全部系统模块 + AI叙事生成 + 完整游戏逻辑
"""
import json
import random
import logging
from .db import (get_player, save_player, create_player, player_exists,
                 get_npcs, get_npc, create_npc, update_npc,
                 get_skills, create_skill, update_skill,
                 get_items, create_item, get_followers,
                 get_world, create_world_faction,
                 add_intel, get_intelligence, cleanup_expired_intel)
from .ai_narrator import generate_narrative_ai
from .db import init_npc_data
from .tech_tree import init_tech_for_player
from .intelligence import (generate_intel, classify_intel, INTEL_CATEGORIES,
                            RELIABILITY_GRADES, INTEL_CHANNELS, get_intel_reliability_bonus)
from .grudge import (trigger_grudge, check_grudge_revenge, try_resolve_grudge,
                      get_narrative_hint, grudge_to_tags)
from .items import (evaluate_gift_match, apply_equipment_bonus, use_poison,
                     check_item_risk, create_item as make_item, ITEM_CATEGORIES)
from .followers import (create_follower, use_follower_action, check_loyalty_change,
                         check_follower_death_or_betray, get_follower_cap, FOLLOWER_TYPES)
from .letters import (generate_letter, should_send_letter, format_letter_for_display,
                       handle_reply_command, get_travel_time, check_letter_risk)
from .romance import (visit_pleasure, harem_action as do_harem_action,
                       get_favor_level, change_favor, execute_court_struggle,
                       pregnancy_check, childbirth, get_children, grow_children,
                       trigger_romance_event, PLEASURE_VENUES, FULL_HAREM_ACTIONS,
                       FAVOR_LEVELS, HAREM_RANKS)
from .achievements import (evaluate_ranking, format_ranking, check_milestones,
                            generate_memory, create_keepsake)
from .business_advanced import (execute_advanced_strategy, get_available_strategies,
                                 get_market_conditions, ADVANCED_STRATEGIES)
from .shuihuo import (should_trigger_ip_event, get_moral_choice,
                       execute_location_action, IP_INFO, LOCATION_ECOLOGY)
from .adultery import (start_seduction, advance_seduction, ADULTERY_TARGETS,
                        ADULTERY_ACTIONS, get_husband_reaction,
                        trigger_adultery_event, SEDUCTION_STAGES)
from .enhancements import (get_personality_bonus, get_market_impact,
                            get_business_modifier_from_market, get_exam_prep_action,
                            trigger_prep_event, add_exposure, decay_exposure,
                            check_mokan_promotion, get_grey_income)

logger = logging.getLogger(__name__)

# ============================================================
# 常量定义
# ============================================================

LEVEL_ORDER = ["拙劣", "平庸", "普通", "优良", "卓越"]
ALERT_ORDER = ["低", "中", "高"]
POWER_ORDER = ["微末", "小吏", "地方", "朝堂", "权倾"]
YESNO_ORDER = ["低", "中", "高"]
BOND_ORDER = ["仇视", "疏远", "寻常", "友善", "至交"]
SKILL_ORDER = ["未涉猎", "略知一二", "初窥门径", "登堂入室", "融会贯通"]
HEALTH_ORDER = ["垂危", "病弱", "略乏", "康健"]
TREND_VALUES = {"趋降": -1, "稳固": 0, "趋升": 1}
RISK_ORDER = ["安全", "风声", "注意", "立案"]
PRESTIGE_ORDER = ["声名狼藉", "默默无闻", "小有名气", "众望所归", "天下景仰"]
PERSONALITY_DIMS = {
    '义利': ['利己', '中正', '义行'],
    '刚柔': ['阴柔', '中正', '刚直'],
    '宽狭': ['褊狭', '中正', '宽厚'],
    '胆勇': ['怯懦', '中正', '勇烈'],
}

# 成功率阈值
SUCCESS_THRESHOLD = {"极难": 20, "困难": 40, "普通": 60, "容易": 80, "必定": 100}

# 行动精力消耗表
ENERGY_COST = {
    "日常": 3, "功名": 5, "经营": 4, "战斗": 7,
    "犯罪": 5, "风月": 4, "社交": 3, "查询": 1, "过月": 0,
    "科举": 5, "研发": 6, "情报": 4, "随从": 3, "物品": 2, "后宫": 5, "备考": 4,
}

# 身份基础属性
IDENTITY_BASE = {
    "宋": {
        "平民": {"intelligence":"平庸","military":"平庸","politics":"拙劣","alertness":"低","charm":"平庸","malice":"中","greed":"低","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":5},
        "商贾": {"intelligence":"普通","military":"平庸","politics":"平庸","alertness":"中","charm":"普通","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":50},
        "书生": {"intelligence":"优良","military":"拙劣","politics":"平庸","alertness":"低","charm":"普通","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":10},
        "宦官": {"intelligence":"优良","military":"平庸","politics":"优良","alertness":"高","charm":"平庸","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"地方","money":100},
        "妃嫔": {"intelligence":"优良","military":"拙劣","politics":"优良","alertness":"高","charm":"优良","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":30},
    },
    "金": {
        "平民": {"intelligence":"平庸","military":"平庸","politics":"拙劣","alertness":"低","charm":"平庸","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":5},
        "猛安": {"intelligence":"普通","military":"优良","politics":"平庸","alertness":"中","charm":"普通","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":80},
        "谋克": {"intelligence":"平庸","military":"普通","politics":"拙劣","alertness":"中","charm":"平庸","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":30},
        "勃极烈属官": {"intelligence":"优良","military":"平庸","politics":"优良","alertness":"高","charm":"普通","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"地方","money":100},
    },
    "辽": {
        "平民": {"intelligence":"平庸","military":"平庸","politics":"拙劣","alertness":"低","charm":"平庸","malice":"中","greed":"低","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":5},
        "详稳": {"intelligence":"普通","military":"优良","politics":"平庸","alertness":"中","charm":"普通","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":60},
        "南面官": {"intelligence":"优良","military":"拙劣","politics":"优良","alertness":"高","charm":"普通","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":50},
    },
    "西夏": {
        "平民": {"intelligence":"平庸","military":"平庸","politics":"拙劣","alertness":"低","charm":"平庸","malice":"中","greed":"低","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":5},
        "铁鹞子": {"intelligence":"普通","military":"优良","politics":"平庸","alertness":"中","charm":"普通","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":40},
        "蕃汉官僚": {"intelligence":"优良","military":"平庸","politics":"优良","alertness":"高","charm":"普通","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"地方","money":90},
    },
    "蒙古": {
        "部民": {"intelligence":"平庸","military":"平庸","politics":"拙劣","alertness":"低","charm":"平庸","malice":"中","greed":"低","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":3},
        "那可儿": {"intelligence":"普通","military":"普通","politics":"拙劣","alertness":"中","charm":"普通","malice":"中","greed":"中","loyalty_court":"中","loyalty_faction":"中","power":"微末","money":10},
        "萨满": {"intelligence":"优良","military":"平庸","politics":"普通","alertness":"高","charm":"普通","malice":"中","greed":"高","loyalty_court":"中","loyalty_faction":"中","power":"小吏","money":20},
    },
}

# 特质修正表
TRAIT_MODS = {
    "书香门第": {"智力": "+1"},
    "寒窗苦读": {"智力": "+1"},
    "过目不忘": {},
    "宗族荫庇": {"权力值": "+1"},
    "西军将门": {"军事": "+1", "政治": "-1"},
    "世袭武官": {},
    "边关历练": {"警惕": "+1"},
    "死里逃生": {},
    "商贾血脉": {"金钱": "+50"},
    "江湖阅历": {"警惕": "+1"},
    "市井百晓": {"权力值": "-1"},
    "三教九流": {},
    "民间神医": {"政治": "-1"},
    "内侍收养": {},
    "天生反骨": {"官家忠诚": "=低"},
    "谲诈之才": {"阴毒": "=高"},
    "铁石心肠": {},
    "灵觉敏锐": {"警惕": "+1"},
    "坚忍不拔": {},
    "铁骨铜筋": {"智力": "-1"},
    "敏捷如猿": {},
    "鹤发童颜": {},
    "八面玲珑": {},
    "仗义疏财": {},
    "眉目如画": {"魅力": "+1"},
    "气度非凡": {},
    "玉树临风": {"魅力": "+1"},
    "谈吐不凡": {},
    "顾盼生辉": {"魅力": "+1"},
    "威仪凛然": {},
    "长袖善舞": {},
}

# 技能初始表
SKILL_INIT = {
    "经义": "未涉猎", "策论": "未涉猎", "律法": "未涉猎", "水利": "未涉猎",
    "兵学": "未涉猎", "商道": "未涉猎", "医术": "未涉猎", "百工": "未涉猎",
}

IDENTITY_SKILL_BONUS = {
    "书生": {"经义": "略知一二", "策论": "略知一二"},
    "商贾": {"商道": "略知一二"},
    "宦官": {"律法": "略知一二", "策论": "略知一二"},
    "妃嫔": {"经义": "略知一二"},
    "猛安": {"兵学": "略知一二"},
    "铁鹞子": {"兵学": "略知一二"},
    "详稳": {"兵学": "略知一二"},
    "南面官": {"律法": "略知一二"},
    "蕃汉官僚": {"律法": "略知一二"},
    "勃极烈属官": {"策论": "略知一二"},
    "萨满": {"医术": "略知一二"},
}

TRAIT_SKILL_BONUS = {
    "书香门第": {"经义": "略知一二", "策论": "略知一二"},
    "西军将门": {"兵学": "略知一二"},
    "商贾血脉": {"商道": "略知一二"},
    "民间神医": {"医术": "略知一二"},
}

# 暴露风险升档概率
EXPOSURE_PROMOTE = {
    "通奸": {"安全": 0.25, "风声": 0.30, "注意": 0.65},
    "走私": {"安全": 0.25, "风声": 0.30, "注意": 0.35},
    "贪污": {"安全": 0.30, "风声": 0.65, "注意": 0.70},
    "谋杀": {"安全": 0.70, "风声": 0.75, "注意": 1.0},
    "伪造": {"安全": 0.25, "风声": 0.30, "注意": 0.35},
}

# 好感度变化
BOND_CHANGE_MAP = {
    "赠礼": {"shift": 1, "prob": 0.60},
    "帮助": {"shift": 1, "prob": 0.50},
    "深度帮助": {"shift": 1, "prob": 0.80},
    "失信": {"shift": -1, "prob": 0.70},
    "侮辱": {"shift": -1, "prob": 0.85},
    "重大背叛": {"shift": -2, "prob": 0.90},
    "背叛": {"shift": -1, "prob": 0.80},
    "求助被拒": {"shift": -1, "prob": 0.40},
}

# 禁止词
FORBIDDEN_KEYWORDS = [
    "土地革命", "民主", "共产主义", "社会主义", "资本",
    "核武器", "火箭", "量子", "激光", "互联网",
    "坦克", "机枪", "步枪", "手枪", "手榴弹", "炸药包",
    "跳街舞", "Rap", "电音", "DJ",
    "刺杀赵佶", "刺杀宋徽宗", "刺杀皇帝", "弑君",
    "穿越", "系统", "面板", "任务列表", "等级", "经验值",
]

# 历史事件
HISTORICAL_EVENTS = {
    "宣和二年正月": "宋金'海上之盟'谈判启动",
    "宣和二年二月": "花石纲扰民加剧，东南民怨沸腾",
    "宣和二年三月": "王黼进位少傅，朝堂暗流涌动",
    "宣和二年四月": "辽国使臣到开封，求援抗金",
    "宣和二年五月": "方腊在睦州暗中筹备起兵",
    "宣和二年六月": "方腊起兵，自称'圣公'，建元'永乐'",
    "宣和二年七月": "方腊军连克睦州、歙州，声势浩大",
    "宣和二年八月": "徽宗震怒，调兵遣将",
    "宣和二年九月": "童贯率西军十五万南下平叛",
    "宣和二年十月": "宋江等三十六人横行河朔京东",
    "宣和二年十一月": "童贯大军抵江宁，分路进击",
    "宣和二年十二月": "徽宗下诏罢花石纲；金军大破辽上京",
}

# 随机事件
RANDOM_EVENTS = [
    {"type": "天灾", "prob": 0.05, "desc": "今年旱情加剧，粮价飞涨"},
    {"type": "民变", "prob": 0.03, "desc": "走投无路的流民聚众哄抢粮仓"},
    {"type": "朝堂", "prob": 0.08, "desc": "朝中有人上书弹劾，暗流涌动"},
    {"type": "市井", "prob": 0.10, "desc": "瓦舍中传来一个有趣的消息"},
    {"type": "江湖", "prob": 0.06, "desc": "有人在暗处打探你的消息"},
    {"type": "奇遇", "prob": 0.03, "desc": "你遇到了一位不寻常的人"},
    {"type": "家事", "prob": 0.05, "desc": "家中传来消息，需要你拿主意"},
]

# 月份列表
MONTHS = ["正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]


# ============================================================
# 辅助函数
# ============================================================

def level_shift(current, order, delta):
    """在档位序列上移动"""
    if current not in order:
        return current
    idx = order.index(current)
    new_idx = max(0, min(len(order)-1, idx + delta))
    return order[new_idx]

def apply_trait_mod(attrs, trait):
    """应用特质修正到属性字典"""
    mods = TRAIT_MODS.get(trait, {})
    for k, v in mods.items():
        if k == "金钱":
            if v.startswith("+"):
                attrs["money"] = attrs.get("money", 0) + int(v[1:])
            elif v.startswith("-"):
                attrs["money"] = max(0, attrs.get("money", 0) - int(v[1:]))
            continue
        if k == "权力值":
            order = POWER_ORDER
        elif k == "警惕":
            order = ALERT_ORDER
        elif k in ("阴毒", "贪欲", "官家忠诚", "派系忠诚"):
            order = YESNO_ORDER
        else:
            order = LEVEL_ORDER
        current = attrs.get(k, order[1] if len(order) > 2 else "中")
        if current not in order:
            current = order[1] if len(order) > 2 else "中"
        if v.startswith("+"):
            idx = order.index(current)
            attrs[k] = order[min(idx + 1, len(order) - 1)]
        elif v.startswith("-"):
            idx = order.index(current)
            attrs[k] = order[max(idx - 1, 0)]
        elif v.startswith("="):
            attrs[k] = v[1:]

def get_next_month(current_time):
    """计算下一月"""
    try:
        parts = current_time.replace("宣和二年", "").replace("宣和三年", "").replace("宣和四年", "")
        year_prefix = current_time[:4] if current_time.startswith("宣和") else "宣和二"
        year_num = int(current_time[2:4]) if len(current_time) > 4 else 2
        month_str = current_time[-2:] if current_time[-1] == "月" else current_time[-3:]
        month_str = month_str.replace("月", "")

        if month_str in MONTHS:
            idx = MONTHS.index(month_str)
            if idx == 11:
                return f"宣和{year_num+1}年正月"
            else:
                return f"宣和{year_num}年{MONTHS[idx+1]}"
    except:
        pass
    return "宣和二年二月"

def format_status_line(player, action_type=""):
    """格式化状态行"""
    status = f"【状态】时：{player['current_time']} | 金：{int(player['money'])}贯 | 精：{player['energy']}/{player['energy_cap']} | 身：{player['health']}"
    if player.get('health_trend') and player['health_trend'] != '稳固':
        status += f"·{player['health_trend']}"
    status += f" | 地：{player['location']}"
    status += f"\n职：{player['official_rank']} | 势：{player['power']} | 望：{player['prestige']}"

    EXT_MAP = {
        "社交": "魅力", "婚恋": "魅力", "招揽": "魅力",
        "谋划": "智力", "识破": "智力", "学术": "智力",
        "指挥": "军事", "战斗": "军事", "练兵": "军事",
        "政务": "政治", "派系": "政治", "权谋": "政治",
    }
    ATTR_FIELD = {"智力": "intelligence", "军事": "military", "政治": "politics", "魅力": "charm"}
    ext_attr = EXT_MAP.get(action_type, '')
    if ext_attr and ext_attr in ATTR_FIELD:
        attr_val = player.get(ATTR_FIELD[ext_attr], '')
        if attr_val:
            status += f" | {ext_attr[:1]}：{attr_val}"

    return status


# ============================================================
# 一、角色创建
# ============================================================

def char_create(user_id, name, gender, age, faction, identity, trait, location=""):
    """完整角色创建流程"""
    if player_exists(user_id):
        return {"error": "角色已存在"}

    age = int(age)
    if age < 14:
        age = 14

    # 1. 基础属性
    base = IDENTITY_BASE.get(faction, IDENTITY_BASE["宋"]).get(identity, IDENTITY_BASE["宋"]["平民"])
    attrs = dict(base)

    # 2. 特质修正
    apply_trait_mod(attrs, trait)

    # 3. 人望
    prestige_details = {
        "官声": "默默无闻", "民望": "默默无闻",
        "文名": "默默无闻", "武名": "默默无闻",
        "富名": "默默无闻", "江湖名": "默默无闻"
    }
    if identity == "书生":
        prestige_details["文名"] = "小有名气"
    if identity == "商贾":
        prestige_details["富名"] = "小有名气"
    if trait == "天生反骨":
        prestige_details["江湖名"] = "小有名气"
    if trait == "谲诈之才":
        for k in prestige_details:
            prestige_details[k] = "声名狼藉"

    max_prestige = "默默无闻"
    for v in prestige_details.values():
        if v in PRESTIGE_ORDER and max_prestige in PRESTIGE_ORDER:
            if PRESTIGE_ORDER.index(v) > PRESTIGE_ORDER.index(max_prestige):
                max_prestige = v

    # 4. 精力上限
    energy_cap = 30
    if trait == "寒窗苦读":
        energy_cap -= 2
    if trait == "灵觉敏锐":
        energy_cap -= 2
    if trait == "敏捷如猿":
        energy_cap -= 5
    energy_cap = max(10, energy_cap)

    # 5. 默认地点
    if not location:
        default_locs = {
            "平民": "东京开封府", "商贾": "东京开封府",
            "书生": "东京开封府", "宦官": "东京开封府",
            "妃嫔": "东京开封府",
            "猛安": "会宁府", "谋克": "会宁府",
            "勃极烈属官": "会宁府",
            "详稳": "上京临潢府", "南面官": "燕京",
            "铁鹞子": "兴庆府", "蕃汉官僚": "兴庆府",
            "部民": "斡难河畔", "那可儿": "斡难河畔",
            "萨满": "斡难河畔",
        }
        location = default_locs.get(identity, "东京开封府")

    # 6. 写入player表
    player_data = {
        'name': name, 'gender': gender, 'age': age,
        'identity': identity, 'faction': faction,
        'traits': json.dumps([trait], ensure_ascii=False),
        'intelligence': attrs.get('intelligence', '平庸'),
        'military': attrs.get('military', '平庸'),
        'politics': attrs.get('politics', '拙劣'),
        'alertness': attrs.get('alertness', '低'),
        'charm': attrs.get('charm', '平庸'),
        'malice': attrs.get('malice', '中'),
        'greed': attrs.get('greed', '中'),
        'loyalty_court': attrs.get('loyalty_court', '中'),
        'loyalty_faction': attrs.get('loyalty_faction', '中'),
        'money': attrs.get('money', 0),
        'health': '康健', 'health_trend': '稳固',
        'health_status': '[]',
        'energy': energy_cap, 'energy_cap': energy_cap,
        'official_rank': '白身', 'troops': 0,
        'prestige': max_prestige,
        'prestige_official': prestige_details['官声'],
        'prestige_civilian': prestige_details['民望'],
        'prestige_literary': prestige_details['文名'],
        'prestige_martial': prestige_details['武名'],
        'prestige_wealth': prestige_details['富名'],
        'prestige_jianghu': prestige_details['江湖名'],
        'power': attrs.get('power', '微末'),
        'exposure_risk': '安全',
        'personality_yili': '中正', 'personality_gangrou': '中正',
        'personality_kuanxia': '中正', 'personality_danyong': '中正',
        'yili_actions': 0, 'gangrou_actions': 0,
        'kuanxia_actions': 0, 'danyong_actions': 0,
        'personal_desire': '', 'desire_stage': '未启程',
        'location': location,
        'current_time': '宣和二年正月',
        'month_days_elapsed': 0, 'total_months_played': 0,
        'crime_this_month': 0, 'event_count_this_month': 0,
        'acquisitions': '[]',
    }
    create_player(user_id, player_data)

    # 7. 写入技能表
    skills = dict(SKILL_INIT)
    for k, v in IDENTITY_SKILL_BONUS.get(identity, {}).items():
        skills[k] = v
    for k, v in TRAIT_SKILL_BONUS.get(trait, {}).items():
        if skills.get(k, "未涉猎") == "未涉猎":
            skills[k] = v
        else:
            idx = SKILL_ORDER.index(skills[k]) if skills[k] in SKILL_ORDER else 0
            bonus_idx = SKILL_ORDER.index(v) if v in SKILL_ORDER else 0
            skills[k] = SKILL_ORDER[max(idx, bonus_idx)]

    for skill_name, level in skills.items():
        create_skill(user_id, skill_name, level)

    # 8. 批量导入该势力NPC（300+）
    try:
        npc_count = init_npc_data(user_id, faction)
        logger.info(f"NPC导入完成: {npc_count}人")
    except Exception as e:
        logger.warning(f"NPC导入失败，使用简化NPC: {e}")
        # 降级：至少创建一个NPC
        create_npc(user_id, {
            'name': '陈伯渊', 'bond': '友善',
            'tags': json.dumps(["同龄好友"], ensure_ascii=False),
            'note': f"{name}的知己",
            'npc_identity': identity, 'npc_power': attrs.get('power', '微末'),
            'npc_faction': faction, 'npc_age': age,
            'npc_health': '康健',
            'npc_personality': json.dumps({"义利": "中正", "刚柔": "中正"}, ensure_ascii=False),
            'npc_greed': '中', 'npc_malice': '低', 'npc_loyalty': '中',
            'npc_intelligence': '普通', 'npc_military': '平庸', 'npc_alertness': '中',
        })

    # 9. 初始化科技树
    try:
        from .tech_tree import init_tech_for_player
        init_tech_for_player(user_id)
        logger.info("科技树初始化完成")
    except Exception as e:
        logger.warning(f"科技树初始化失败: {e}")

    # 10. 返回角色面板
    player_data['skills'] = skills
    return player_data


# ============================================================
# 二、行动处理
# ============================================================

def classify_action(user_input):
    """简单分类玩家行动类型"""
    text = user_input.lower()
    if any(w in text for w in ["过月", "结算", "结束本月"]):
        return "过月"
    if any(w in text for w in ["查询", "查看", "属性", "技能", "人脉", "好感", "人望", "交情", "排名"]) and not any(w in text for w in ["科技", "研发"]):
        return "查询"
    if any(w in text for w in ["战斗", "攻击", "打仗", "出征", "布阵", "杀"]):
        return "战斗"
    if any(w in text for w in ["研发", "研究", "科技", "改进", "发明"]):
        return "研发"
    if any(w in text for w in ["科举", "考试", "发解试", "省试", "殿试"]):
        return "科举"
    if any(w in text for w in ["买", "卖", "经营", "盘账", "商", "产业"]):
        return "经营"
    # 情报类
    if any(w in text for w in ["打探", "刺探", "情报", "线报", "风声"]):
        return "情报"
    # 随从类
    if any(w in text for w in ["随从", "护卫", "仆役", "谋士", "商帮", "招募", "遣散"]):
        return "随从"
    # 赠礼/物品类
    if any(w in text for w in ["赠给", "赠送", "送礼物", "下毒", "用药", "装备"]):
        return "物品"
    if any(w in text for w in ["偷", "杀", "走私", "贪污", "伪造", "犯罪"]):
        return "犯罪"
    if any(w in text for w in ["青楼", "风月", "约会", "后官"]):
        return "风月"
    if any(w in text for w in ["侍寝", "诏驾", "献艺", "宫斗", "争宠", "婕妤", "嫔", "妃", "冷官"]):
        return "后宫"
    if any(w in text for w in ["拜访", "结交", "社交", "游说", "赠礼", "宴请"]):
        return "社交"
    if any(w in text for w in ["读书", "练兵", "研读", "修炼", "学习", "练武"]):
        return "功名"
    return "日常"


def action_energy_check(player, action_desc, energy_cost):
    """精力检查"""
    for kw in FORBIDDEN_KEYWORDS:
        if kw in action_desc:
            return {"can_act": False, "reason": f"天罚：行为严重违制（含'{kw}'）", "new_energy": player['energy']}

    current = player['energy']
    if current < energy_cost:
        return {"can_act": False, "reason": f"精力不足(当前{current}，需要{energy_cost})，请过月或减少行动", "new_energy": current}
    return {"can_act": True, "reason": "", "new_energy": current - energy_cost}


def action_success_rate(player_attr, skill_level='未涉猎', investment='一般', interference='无', synergy=False):
    """成功率判定"""
    base_idx = 2
    attr_idx = LEVEL_ORDER.index(player_attr) if player_attr in LEVEL_ORDER else 2
    base_idx -= (attr_idx - 2)
    base_idx = max(0, min(4, base_idx))

    skill_idx = SKILL_ORDER.index(skill_level) if skill_level in SKILL_ORDER else 0
    if skill_idx == 0:
        base_idx = min(4, base_idx + 1)
    elif skill_idx >= 3:
        base_idx = max(0, base_idx - 1)
    elif skill_idx >= 4:
        base_idx = max(0, base_idx - 2)

    if investment == "充足":
        base_idx = max(0, base_idx - 1)
    elif investment == "不足":
        base_idx = min(4, base_idx + 1)

    if interference == "轻微":
        base_idx = min(4, base_idx + 1)
    elif interference == "严重":
        base_idx = min(4, base_idx + 2)

    if synergy and skill_idx >= 2:
        base_idx = max(0, base_idx - 1)

    base_idx = max(0, min(4, base_idx))
    final_level = list(SUCCESS_THRESHOLD.keys())[base_idx]
    threshold = SUCCESS_THRESHOLD[final_level]

    roll = random.randint(1, 100)
    success = roll <= threshold

    return {
        "success_level": final_level,
        "threshold": threshold,
        "roll": roll,
        "success": success,
        "margin": threshold - roll
    }


def action_exposure_risk(current_risk, crime_type=''):
    """暴露风险判定"""
    current_idx = RISK_ORDER.index(current_risk) if current_risk in RISK_ORDER else 0
    promote_probs = EXPOSURE_PROMOTE.get(crime_type, {})
    prob = promote_probs.get(current_risk, 0.20)

    new_idx = current_idx
    if crime_type == "谋杀" and current_risk == "安全":
        r = random.random()
        if r < 0.50:
            new_idx = min(3, current_idx + 2)
        elif r < 0.75:
            new_idx = min(3, current_idx + 1)
    else:
        if random.random() < prob:
            new_idx = min(3, current_idx + 1)

    return {
        "old_risk": current_risk,
        "new_risk": RISK_ORDER[new_idx],
        "risk_changed": new_idx != current_idx
    }


def action_bond_change(current_bond, action_type=''):
    """好感度变化"""
    change = BOND_CHANGE_MAP.get(action_type, {"shift": 0, "prob": 0})
    current_idx = BOND_ORDER.index(current_bond) if current_bond in BOND_ORDER else 2

    new_idx = current_idx
    if change["shift"] != 0 and random.random() < change["prob"]:
        new_idx = max(0, min(4, current_idx + change["shift"]))

    return {
        "old_bond": current_bond,
        "new_bond": BOND_ORDER[new_idx],
        "bond_changed": new_idx != current_idx
    }


def action_npc_decision(npc_loyalty, npc_greed, npc_malice, npc_power, player_power, player_bond, threat=False):
    """NPC决策判定"""
    if threat:
        return {"decision": "直接拒绝", "reason": "生存底线"}
    if npc_loyalty == '高':
        if player_bond in ['友善', '至交']:
            return {"decision": "全心全意执行", "reason": "忠诚+好感"}
        return {"decision": "全心全意执行", "reason": "忠诚导向"}

    npc_pi = POWER_ORDER.index(npc_power) if npc_power in POWER_ORDER else 0
    player_pi = POWER_ORDER.index(player_power) if player_power in POWER_ORDER else 0

    if player_pi >= npc_pi + 2 and npc_loyalty != '高':
        return {"decision": "被迫服从", "reason": "权力压制"}
    if npc_greed == '高' and npc_loyalty in ['低', '中']:
        return {"decision": "阳奉阴违", "reason": "贪欲驱动"}
    if npc_malice == '高' and npc_loyalty == '低':
        return {"decision": "告密/背叛", "reason": "阴毒+无忠诚"}
    if player_bond in ['友善', '至交']:
        return {"decision": "部分接受", "reason": "好感修正"}
    if npc_loyalty == '中':
        return {"decision": "虚与委蛇", "reason": "观望态度"}
    return {"decision": "直接拒绝", "reason": "利益不符"}


# ============================================================
# 三、过月结算
# ============================================================

def month_settle(user_id):
    """完整过月流程"""
    player = get_player(user_id)
    if not player:
        return {"error": "角色不存在"}

    details = []

    # 1. 收支结算
    income_result = month_income_expense(player, user_id)
    details.append(income_result['summary'])
    player['money'] = income_result['new_money']

    # 2. 好感结算
    bond_result = month_bond_settle(user_id)
    if bond_result['summary'] != '人际关系稳定':
        details.append(bond_result['summary'])

    # 3. 健康结算
    health_result = month_health_settle(player)
    details.append(health_result['details'])
    player['health'] = health_result['new_health']
    player['health_trend'] = health_result['new_trend']
    player['health_status'] = health_result['new_health_status']

    # 4. 精力上限重算
    cap_result = month_energy_cap_recalc(player)
    player['energy_cap'] = int(cap_result['new_energy_cap'])

    # 5. 暴露风险衰减
    exposure_result = month_exposure_decay(player)
    player['exposure_risk'] = exposure_result['new_risk']

    # 6. 性格维度校验
    personality_result = month_personality_check(player)
    if personality_result['changed'] == 'true':
        details.append(personality_result['changes'])
        # 更新性格
        for dim_name, (count, levels) in PERSONALITY_DIMS.items():
            key = f"personality_{dim_name}"
            current = player.get(key, '中正')
            if count >= 3 and current in levels:
                idx = levels.index(current)
                if idx < len(levels) - 1 and random.random() < 0.50:
                    player[key] = levels[idx + 1]
            elif count <= -3 and current in levels:
                idx = levels.index(current)
                if idx > 0 and random.random() < 0.50:
                    player[key] = levels[idx - 1]

    # 6.5 历史大事件
    try:
        from .events import get_event_for_month
        event = get_event_for_month(player.get('current_time', ''))
        if event:
            details.append(f"【{event['type']}】{event['desc']}")
    except ImportError:
        pass

    # 7. 随机事件
    event_result = month_event_trigger(player)
    if event_result['should_trigger'] == 'true':
        details.append(f"【{event_result['event_type']}】{event_result['event_desc']}")
        player['event_count_this_month'] = int(event_result.get('new_event_count', 0))

    # 7.5 科技研发自动推进
    try:
        from .tech_tree import get_tech_status, research_tech, get_research_bonus
        tech_status = get_tech_status(user_id)
        for cat_techs in tech_status.values():
            if isinstance(cat_techs, list):
                for t in cat_techs:
                    if t['status'] == 'researching':
                        rp = random.randint(5, 15)
                        result = research_tech(user_id, t['name'], rp)
                        if result.get('completed'):
                            details.append(f"【科技完成】{t['name']}研发成功！")
        # 应用科技加成
        bonuses = get_research_bonus(user_id)
        if bonuses.get('energy_cap', 0) > 0:
            player['energy_cap'] = int(player.get('energy_cap', 30)) + bonuses['energy_cap']
    except Exception:
        pass

    # 8. 荒废检查
    decay_result = month_decay_check(player, user_id)
    if decay_result['summary'] != '属性技能无荒废':
        details.append(decay_result['summary'])

    # 8.5 仇恨报复检查（过月）
    try:
        npcs = get_npcs(user_id)
        for n in npcs:
            grudge_level = n.get('grudge_level', '')
            if grudge_level:
                revenge = check_grudge_revenge(grudge_level)
                if revenge:
                    details.append(f"【恩怨】{n['name']}({get_narrative_hint(grudge_level)}){revenge['行为']}（{revenge['规模']}事件）")
    except Exception:
        pass

    # 8.6 随从月度检查
    try:
        followers = get_followers(user_id)
        for f in followers:
            result = check_follower_death_or_betray(f)
            if result:
                details.append(f"【随从】{result}")
                from .db import get_db, DATABASE_URL
                conn = get_db()
                ph = '%s' if DATABASE_URL else '?'
                conn.execute(f"UPDATE followers SET loyalty='低' WHERE user_id={ph} AND name={ph}",
                            (user_id, f['name']))
                conn.commit()
                conn.close()
    except Exception:
        pass

    # 8.7 情报过期清理
    try:
        cleaned = cleanup_expired_intel(user_id, player.get('current_time', '宣和二年正月'))
        if cleaned > 0:
            details.append(f"【情报】{cleaned}条过期情报已失效")
    except Exception:
        pass

    # 8.8 书信检查（过月随机触发）
    try:
        npcs = get_npcs(user_id)
        for n in npcs:
            letter_type = should_send_letter(n, player.get('location', ''), player.get('total_months_played', 1))
            if letter_type:
                letter = generate_letter(letter_type, n.get('name', ''), n.get('npc_location', ''))
                if letter:
                    distance = get_travel_time(n.get('npc_location', ''), player.get('location', ''))
                    risk = check_letter_risk(distance)
                    risk_text = f"（风险：{risk['类型']}）" if risk else ""
                    details.append(f"【书信】收到{n['name']}来信——{format_letter_for_display(letter)[:50]}...{risk_text}")
    except Exception:
        pass

    # 8.9 里程碑检查
    try:
        existing = player.get('milestones', '[]')
        if isinstance(existing, str):
            existing = json.loads(existing) if existing else []
        new_ms = check_milestones(player, npcs if 'npcs' in dir() else [], existing)
        if new_ms:
            for ms in new_ms:
                details.append(f"【里程碑】{ms['名称']}——{ms['叙事']}")
            existing.extend([m['名称'] for m in new_ms])
            player['milestones'] = json.dumps(existing, ensure_ascii=False)
    except Exception:
        pass

    # 8.10 子嗣与孕产推进
    try:
        children = get_children(player)
        if children:
            child_events = grow_children(children, player.get('current_time', ''))
            for ce in child_events:
                details.append(f"【子嗣】{ce}")
            player = save_children(player, children)

        # 孕期推进
        if player.get('is_pregnant'):
            preg_months = int(player.get('pregnancy_months', 0)) + 1
            player['pregnancy_months'] = preg_months
            if preg_months >= 10:
                # 分娩
                age = int(player.get('age', 20))
                is_prince_ctx = player.get('identity') == '妃嫔'
                safe, gender, birth_desc = childbirth(age, is_prince_ctx)
                player['is_pregnant'] = False
                player['pregnancy_months'] = 0
                details.append(f"【产子】{birth_desc}")
                if safe and gender:
                    child_name = f"{random.choice(['元','永','景','瑞'])}{random.choice(['昭','成','宁','安'])}"
                    child = create_child(child_name, gender, player.get('current_time', ''), is_prince_ctx)
                    children.append(child)
                    player = save_children(player, children)
            elif preg_months >= 3:
                details.append(f"【有孕】已怀胎{preg_months}月")
    except Exception:
        pass

    # 9. 重置月度计数器
    player['current_time'] = get_next_month(player['current_time'])
    player['energy'] = player['energy_cap']
    player['month_days_elapsed'] = 0
    player['crime_this_month'] = 0
    player['event_count_this_month'] = 0
    player['yili_actions'] = 0
    player['gangrou_actions'] = 0
    player['kuanxia_actions'] = 0
    player['danyong_actions'] = 0
    player['total_months_played'] += 1

    # 9.5 磨勘晋升检查
    try:
        months_in_office = player.get('total_months_played', 0)
        if months_in_office > 0 and months_in_office % 12 == 0:
            promoted, new_rank, mokan_desc = check_mokan_promotion(player, months_in_office)
            if promoted:
                player['official_rank'] = new_rank
                power_map = {"县尉":"小吏","知县":"小吏","通判":"地方",
                    "知州":"地方","转运使":"地方","郎中":"朝堂",
                    "侍郎":"朝堂","尚书":"朝堂","宰执":"权倾"}
                player['power'] = power_map.get(new_rank, player.get('power','微末'))
                details.append(f"【升迁】{mokan_desc}")
    except Exception:
        pass

    # 9.6 暴露风险衰减
    try:
        orig_risk = player.get('exposure_risk', '安全')
        risk_order = ["安全", "风声", "注意", "立案"]
        if orig_risk in risk_order:
            orig_idx = risk_order.index(orig_risk)
            if player.get('crime_this_month', 0) == 0 and orig_idx > 0:
                if random.random() < 0.4:
                    player['exposure_risk'] = risk_order[orig_idx - 1]
                    details.append(f"【风声】暴露风险降至「{player['exposure_risk']}」")
    except Exception:
        pass

    save_player(user_id, player)
    # 生成状态行
    status_line = format_status_line(player)

    return {
        "narrative": "；".join([d for d in details if d]),
        "status_line": status_line,
        "player": player,
        "new_time": player['current_time'],
        "new_energy": player['energy'],
    }


def month_income_expense(player, user_id):
    money = float(player.get('money', 0))
    power = player.get('power', '微末')
    greed = player.get('greed', '中')

    LIVING_COST = {"微末": 1, "小吏": 5, "地方": 30, "朝堂": 100, "权倾": 300}
    OFFICIAL_SALARY = {"小吏": 3, "地方": 20, "朝堂": 80, "权倾": 200}
    BIZ_INCOME = {"盈利": 8, "持平": 0, "亏损": -5}

    income = 0.0
    expense = 0.0
    details = []

    if power in OFFICIAL_SALARY:
        income += OFFICIAL_SALARY[power]
        details.append(f"官俸+{OFFICIAL_SALARY[power]}贯")

    items = get_items(user_id, '产业')
    for item in items:
        status = item.get('status', '')
        name = item.get('name', '')
        if status in BIZ_INCOME:
            val = BIZ_INCOME[status]
            if val > 0:
                income += val
                details.append(f"{name}盈利+{val}贯")
            elif val < 0:
                expense += abs(val)
                details.append(f"{name}亏损-{abs(val)}贯")

    living = LIVING_COST.get(power, 1)
    expense += living
    details.append(f"生活开支-{living}贯")

    followers = get_followers(user_id)
    for f in followers:
        sal = float(f.get('salary', 0))
        if sal > 0:
            expense += sal
            details.append(f"随从{f.get('name','')}薪-{sal}贯")

    if greed in ['高', '偏高']:
        luxury = round(money * 0.1, 1)
        if luxury > 0.5:
            expense += luxury
            details.append(f"奢靡习气-{luxury}贯")

    new_money = round(max(0, money + income - expense), 1)

    # 灰色收入（贪欲驱动）
    grey = 0
    if greed == "高" and power not in ("微末",):
        grey = get_grey_income(player.get('official_rank', '白身'), greed, power)
        new_money += grey
        if grey > 0:
            details.append(f"灰色收入+{grey}贯（隐）")

    # 市场环境联动
    try:
        market = get_market_impact(player)
        if market:
            details.append("市情：" + "；".join([f"{n}" for n, _ in market[:2]]))
    except Exception:
        pass

    return {
        "income": income, "expense": expense,
        "new_money": new_money,
        "summary": "；".join(details) if details else "本月无收支变动"
    }


def month_health_settle(player):
    health = player.get('health', '康健')
    trend = player.get('health_trend', '稳固')
    health_status = json.loads(player.get('health_status', '[]'))
    age = int(player.get('age', 18))
    had_combat = False
    had_rest = True

    current_idx = HEALTH_ORDER.index(health) if health in HEALTH_ORDER else 3
    trend_val = TREND_VALUES.get(trend, 0)

    if had_combat:
        trend_val -= 1
    if had_rest:
        trend_val += 1
    if age >= 51:
        trend_val -= 1
    if current_idx < 3:
        trend_val += 1
    if had_rest and current_idx < 3:
        trend_val += 1

    new_idx = current_idx
    if trend_val >= 2:
        new_idx = min(3, current_idx + 1)
        new_trend = "稳固"
    elif trend_val <= -2:
        new_idx = max(0, current_idx - 1)
        new_trend = "稳固"
    elif trend_val == 1:
        new_trend = "趋升"
    elif trend_val == -1:
        new_trend = "趋降"
    else:
        new_trend = "稳固"

    healed = []
    remaining = []
    for inj in health_status:
        if isinstance(inj, str):
            remaining.append(inj)
        elif isinstance(inj, dict):
            months_left = inj.get('months_left', 0) - 1
            if months_left <= 0:
                healed.append(inj.get('name', '某伤病'))
            else:
                inj['months_left'] = months_left
                remaining.append(inj)

    if age >= 41 and random.random() < 0.03:
        remaining.append({"name": "旧恙复发(轻)", "months_left": 1})
    if age >= 51 and random.random() < 0.05:
        remaining.append({"name": "重疾初起", "months_left": 3})

    parts = []
    if new_idx != current_idx:
        parts.append(f"健康由{HEALTH_ORDER[current_idx]}变为{HEALTH_ORDER[new_idx]}")
    if healed:
        parts.append(f"伤病痊愈：{'、'.join(healed)}")

    energy_cap_map = {"康健": 0, "略乏": 0, "病弱": -5, "垂危": -10}

    return {
        "new_health": HEALTH_ORDER[new_idx],
        "new_trend": new_trend,
        "new_health_status": json.dumps(remaining, ensure_ascii=False),
        "details": "；".join(parts) if parts else "身体状况无变化",
        "energy_cap_modifier": energy_cap_map.get(HEALTH_ORDER[new_idx], 0)
    }


def month_bond_settle(user_id):
    npcs = get_npcs(user_id)
    changes = []
    for npc in npcs:
        name = npc.get('name', '')
        bond = npc.get('bond', '寻常')
        months_no = int(npc.get('months_no_interact', 0)) + 1

        # 更新无互动月数
        update_npc(npc['id'], {'months_no_interact': months_no})

        new_bond = bond
        changed = False

        if bond in ['友善', '至交'] and months_no >= 3:
            if random.random() < 0.40:
                idx = BOND_ORDER.index(bond) if bond in BOND_ORDER else 2
                new_bond = BOND_ORDER[max(0, idx - 1)]
                changed = True

        if bond == '仇视' and months_no >= 6:
            if random.random() < 0.15:
                idx = BOND_ORDER.index(bond) if bond in BOND_ORDER else 2
                new_bond = BOND_ORDER[min(4, idx + 1)]
                changed = True

        if changed:
            update_npc(npc['id'], {'bond': new_bond, 'months_no_interact': 0})
            changes.append(f"与{name}{bond}→{new_bond}")

    summary = "；".join([f"与{c}" for c in changes]) if changes else "人际关系稳定"
    return {"changes": changes, "summary": summary}


def month_decay_check(player, user_id):
    skills = get_skills(user_id)
    decays = []
    for skill in skills:
        mal = int(skill.get('months_at_level', 0)) + 1
        level = skill.get('level', '未涉猎')
        update_skill(skill['id'], {'months_at_level': mal})
        if mal >= 6 and level in SKILL_ORDER and level != '未涉猎':
            if random.random() < 0.40:
                idx = SKILL_ORDER.index(level)
                new_level = SKILL_ORDER[idx - 1]
                decays.append(f"技能{skill['skill_name']}{level}→{new_level}")
                update_skill(skill['id'], {'level': new_level, 'months_at_level': 0})

    summary = "；".join(decays) if decays else "属性技能无荒废"
    return {"summary": summary}


def month_energy_cap_recalc(player):
    base_cap = 30
    # 特质修正
    trait_list = json.loads(player.get('traits', '[]'))
    trait_mod = 0
    if "寒窗苦读" in trait_list:
        trait_mod -= 2
    if "灵觉敏锐" in trait_list:
        trait_mod -= 2
    if "敏捷如猿" in trait_list:
        trait_mod -= 5

    # 健康修正
    health = player.get('health', '康健')
    health_mod = {"康健": 0, "略乏": 0, "病弱": -5, "垂危": -10}.get(health, 0)

    new_cap = base_cap + trait_mod + health_mod
    new_cap = max(10, min(50, new_cap))

    return {"new_energy_cap": str(new_cap)}


def month_exposure_decay(player):
    current_risk = player.get('exposure_risk', '安全')
    crime_this_month = int(player.get('crime_this_month', 0))
    current_idx = RISK_ORDER.index(current_risk) if current_risk in RISK_ORDER else 0
    new_idx = current_idx

    if crime_this_month == 0:
        if current_idx == 1 and random.random() < 0.50:
            new_idx = 0
        elif current_idx == 2 and random.random() < 0.25:
            new_idx = 1

    return {
        "old_risk": current_risk,
        "new_risk": RISK_ORDER[new_idx],
        "risk_changed": new_idx != current_idx
    }


def month_personality_check(player):
    dims = {
        '义利': int(player.get('yili_actions', 0)),
        '刚柔': int(player.get('gangrou_actions', 0)),
        '宽狭': int(player.get('kuanxia_actions', 0)),
        '胆勇': int(player.get('danyong_actions', 0)),
    }
    changes = []
    for dim_name, count in dims.items():
        levels = PERSONALITY_DIMS[dim_name]
        current = player.get(f'personality_{dim_name}', '中正')
        current_idx = levels.index(current) if current in levels else 1
        new_idx = current_idx
        if count >= 3 and current_idx < 2:
            if random.random() < 0.50:
                new_idx = current_idx + 1
        elif count <= -3 and current_idx > 0:
            if random.random() < 0.50:
                new_idx = current_idx - 1
        if new_idx != current_idx:
            changes.append(f"{dim_name}：{levels[current_idx]}→{levels[new_idx]}")

    return {
        "changes": "；".join(changes) if changes else "性格稳固",
        "changed": "true" if changes else "false"
    }


def month_event_trigger(player):
    event_count = int(player.get('event_count_this_month', 0))
    current_time = player.get('current_time', '宣和二年正月')

    if event_count >= 2:
        return {"should_trigger": "false", "event_type": "", "event_desc": ""}

    # 优先检查历史事件
    hist_event = HISTORICAL_EVENTS.get(current_time, '')
    if hist_event:
        new_count = event_count + 1
        return {
            "should_trigger": "true",
            "event_type": "历史",
            "event_desc": hist_event,
            "new_event_count": str(new_count)
        }

    # 随机事件
    for event in RANDOM_EVENTS:
        if random.random() < event['prob']:
            new_count = event_count + 1
            return {
                "should_trigger": "true",
                "event_type": event['type'],
                "event_desc": event['desc'],
                "new_event_count": str(new_count)
            }

    return {"should_trigger": "false", "event_type": "", "event_desc": "", "new_event_count": str(event_count)}


# ============================================================
# 四、战斗系统
# ============================================================

def combat_resolve(player_military, player_troops, enemy_troops, player_skill='未涉猎', terrain='平原'):
    """战斗解析（新版：六阶段系统）"""
    player_v = {
        'military': player_military,
        'intelligence': '普通',
        'troops': player_troops,
        'skills': json.dumps({player_skill: '初窥门径'}) if player_skill != '未涉猎' else '{}',
    }
    from .combat import combat_resolve as new_combat
    enemy_strength = "弱" if enemy_troops < 20 else "普通" if enemy_troops < 100 else "强"
    result = new_combat(player_v, "敌军", enemy_strength)
    return {
        "result": result['result'],
        "casualties": result['casualties'],
        "remaining_troops": max(0, player_troops - result['casualties']),
        "loot_money": result['loot_money'],
        "injury_risk": "低" if result['result'] in ("大胜","胜") else "中",
    }


def combat_injury(injury_risk, player_military='平庸'):
    mil_idx = LEVEL_ORDER.index(player_military) if player_military in LEVEL_ORDER else 1
    RISK_PROB = {"低": 0.15, "中低": 0.25, "中": 0.40, "高": 0.60, "极高": 0.80}
    prob = RISK_PROB.get(injury_risk, 0.40)
    if mil_idx >= 3:
        prob *= 0.7

    if random.random() > prob:
        return {"injured": False, "injury_name": "", "injury_severity": "", "recovery_months": 0}

    SEVERITY_TABLE = [
        (0.40, "轻", ["挫伤", "淤青", "浅层刀伤"], 1),
        (0.35, "中", ["深层刀伤", "骨折", "箭伤"], 2),
        (0.20, "重", ["内伤", "粉碎性骨折", "深度箭伤"], 4),
        (0.05, "致命", ["心肺贯穿", "大动脉出血"], 6),
    ]

    r = random.random()
    for threshold, severity, names, months in SEVERITY_TABLE:
        if r < threshold:
            return {
                "injured": True,
                "injury_name": random.choice(names),
                "injury_severity": severity,
                "recovery_months": months
            }
        r -= threshold

    return {"injured": True, "injury_name": "挫伤", "injury_severity": "轻", "recovery_months": 1}


# ============================================================
# 五、查询系统
# ============================================================

def query_status(user_id, query_type="属性"):
    player = get_player(user_id)
    if not player:
        return {"error": "角色不存在"}

    if query_type in ["属性", "状态"]:
        return {
            "text": f"智力：{player['intelligence']} | 军事：{player['military']} | 政治：{player['politics']} | 魅力：{player['charm']}\n"
                    f"警惕：{player['alertness']} | 贪欲：{player['greed']} | 阴毒：{player['malice']} | 官家忠诚：{player['loyalty_court']}",
            "energy_cost": 1
        }
    elif query_type == "技能":
        skills = get_skills(user_id)
        text = " | ".join([f"{s['skill_name']}：{s['level']}" for s in skills])
        return {"text": text, "energy_cost": 1}
    elif query_type == "人脉":
        npcs = get_npcs(user_id)
        text = " | ".join([f"{n['name']}[{n['bond']}]" for n in npcs])
        return {"text": text, "energy_cost": 1}
    elif query_type == "人望":
        return {
            "text": f"总人望：{player['prestige']} | 官声：{player['prestige_official']} | 民望：{player['prestige_civilian']}\n"
                    f"文名：{player['prestige_literary']} | 武名：{player['prestige_martial']} | 富名：{player['prestige_wealth']} | 江湖名：{player['prestige_jianghu']}",
            "energy_cost": 1
        }
    elif query_type == "收获":
        acq = json.loads(player.get('acquisitions', '[]'))
        if acq:
            return {"text": "；".join(acq[-5:]), "energy_cost": 1}
        return {"text": "暂无显著收获记录", "energy_cost": 1}
    else:
        return format_status_line(player), 0


# ============================================================
# 六、叙事模板生成（预模板，后续接AI）
# ============================================================

NARRATIVE_TEMPLATES = {
    "日常_成功": [
        "你{action}，诸事顺遂，{detail}。",
        "{action}完毕，虽非大功，却也稳妥。{detail}。",
    ],
    "日常_失败": [
        "你{action}，却事与愿违。{detail}。",
        "{action}未竟，徒费心力。{detail}。",
    ],
    "社交_成功": [
        "你{action}，与{npc}相谈甚欢，{detail}。",
        "{npc}对你{action}之举颇为赞赏。{detail}。",
    ],
    "社交_失败": [
        "你{action}，但{npc}反应冷淡。{detail}。",
        "{npc}对你的{action}不以为然。{detail}。",
    ],
    "战斗_大胜": [
        "两军交锋，你{action}，敌军大溃！{detail}。折损了{casualties}人，缴获{loot}贯。",
    ],
    "战斗_胜": [
        "一番鏖战，{action}，终是占了上风。{detail}。折损{casualties}人。",
    ],
    "战斗_僵持": [
        "战况胶着，{action}，双方互有伤亡。{detail}。折损{casualties}人。",
    ],
    "战斗_败": [
        "{action}，却遭败绩。{detail}。折损{casualties}人，局势堪忧。",
    ],
    "战斗_惨败": [
        "兵败如山倒！{action}惨败，{detail}。折损{casualties}人，此战损失惨重。",
    ],
    "功名_成功": [
        "你{action}，文思泉涌，{detail}。考官颔首。",
    ],
    "功名_失败": [
        "你{action}，却才思涩滞，{detail}。名落孙山。",
    ],
    "犯罪_成功": [
        "你{action}，行事隐秘，{detail}。",
    ],
    "犯罪_失败": [
        "你{action}，却走漏了风声。{detail}。",
    ],
}

def generate_narrative(action_type, success, detail="", npc="", action="", casualties=0, loot=0, player=None):
    """生成叙事文本（优先AI，降级模板）"""
    # 尝试AI生成
    try:
        ai_text, ai_used, ai_error = generate_narrative_ai(
            action_type=action_type,
            success=success,
            detail=detail,
            npc=npc,
            action=action,
            casualties=casualties,
            loot=loot,
            player=player,
        )
        if ai_used and ai_text:
            logger.info(f"AI叙事生成成功: {action_type}_{'成功' if success else '失败'}")
            return ai_text
        else:
            logger.warning(f"AI叙事生成失败，降级到模板: {ai_error}")
    except Exception as e:
        logger.warning(f"AI叙事生成异常，降级到模板: {e}")

    # 降级：模板生成
    key = f"{action_type}_{'成功' if success else '失败'}"
    if action_type == "战斗":
        battle_results = {"大胜": "大胜", "胜": "胜", "僵持": "僵持", "败": "败", "惨败": "惨败"}
        for br in battle_results:
            if br in detail or br in str(success):
                key = f"战斗_{br}"
                break
        else:
            key = f"战斗_{'胜' if success else '败'}"

    templates = NARRATIVE_TEMPLATES.get(key, NARRATIVE_TEMPLATES.get(f"日常_{'成功' if success else '失败'}", ["你{action}。{detail}。"]))
    template = random.choice(templates)
    return template.format(action=action, detail=detail, npc=npc, casualties=casualties, loot=loot)


def build_output(player, narrative, action_type, energy_cost=0, harvest_tags="", combat_result=None):
    """
    构建文档P0.4要求的输出格式三件套：
    (消耗：精[X] | 金[X]贯 | 时[X] → 收获：[标签])
    【状态】时：[月] | 金：[X]贯 | 精：[剩余]/[上限] | 身：[状态] | 地：[地点]
    → 本月尚余精力[X]点，你打算继续推进何事？
    """
    # 消耗行
    money_cost = 0
    if combat_result:
        money_cost = combat_result.get('loot_money', 0)
    cost_line = f"（消耗：精{energy_cost}"
    if money_cost > 0:
        cost_line += f" | 金-{abs(money_cost)}贯" if money_cost < 0 else f" | 金+{money_cost}贯"
    cost_line += f" | 时1 → 收获：{harvest_tags or '经验'}）"

    # 状态行（文档格式）
    time_str = player.get('current_time', '宣和二年正月')
    money = int(player.get('money', 0))
    energy = player.get('energy', 0)
    energy_cap = player.get('energy_cap', 30)
    health = player.get('health', '康健')
    loc = player.get('location', '东京开封府')
    status_line = f"【状态】时：{time_str} | 金：{money}贯 | 精：{energy}/{energy_cap} | 身：{health} | 地：{loc}"

    # 引导语
    guide_line = f"→ 本月尚余精力{energy}点，你打算继续推进何事？（或输入具体行动）"

    return cost_line, status_line, guide_line


# ============================================================
# 七、主行动处理入口
# ============================================================

def process_action(user_id, user_input):
    """处理玩家行动的主入口"""
    player = get_player(user_id)
    if not player:
        return {"error": "角色不存在，请先创建角色"}

    action_type = classify_action(user_input)

    # 过月
    if action_type == "过月":
        result = month_settle(user_id)
        return {
            "type": "过月",
            "narrative": result['narrative'],
            "status_line": result['status_line'],
            "player": result['player'],
        }

    # 查询
    if action_type == "查询":
        query_type = "属性"
        if "技能" in user_input:
            query_type = "技能"
        elif "人脉" in user_input or "好感" in user_input:
            query_type = "人脉"
        elif "人望" in user_input:
            query_type = "人望"
        elif "收获" in user_input:
            query_type = "收获"

        result = query_status(user_id, query_type)
        energy_cost = 1
        player['energy'] = max(0, player['energy'] - energy_cost)
        save_player(user_id, {'energy': player['energy']})

        return {
            "type": "查询",
            "narrative": result['text'] if isinstance(result, dict) else result,
            "status_line": format_status_line(player, "查询"),
            "energy_cost": energy_cost,
            "player": player,
        }

    # 科举
    if action_type == "科举":
        from .exam import get_exam_question, grade_answer, get_player_exam_level
        from .enhancements import EXAM_PREP_ACTIONS

        current_time = player.get("current_time", "宣和二年正月")
        is_exam_month = any(m in current_time for m in ["八月", "二月", "三月"])

        # === 非考试月：备考 ===
        if not is_exam_month:
            # 具体备考行动
            for prep_key in EXAM_PREP_ACTIONS:
                if prep_key in user_input:
                    prep = EXAM_PREP_ACTIONS[prep_key]
                    check = action_energy_check(player, user_input, prep["精耗"])
                    if not check['can_act']:
                        return {"type": "科举", "narrative": check['reason'], "player": player}
                    player['energy'] = check['new_energy']
                    if prep.get("金耗"):
                        player['money'] = max(0, player['money'] - prep["金耗"])
                    save_player(user_id, {'energy': player['energy'], 'money': player['money']})
                    return {
                        "type": "备考", "narrative": f"【备考·{prep_key}】\n{prep['效果']}。",
                        "harvest_tags": prep_key, "energy_cost": prep["精耗"], "player": player}

            # 展示备考菜单
            menu = "【科举备考】宣和科举：发解试(秋八月)→省试(春二月)→殿试(三月)\n\n可选行动：\n"
            for k, v in EXAM_PREP_ACTIONS.items():
                c = f"精{v['精耗']}" + (f" 金{v['金耗']}贯" if v.get('金耗') else "")
                menu += f"  • {k}（{c}）—— {v['效果']}\n"
            menu += "\n→ 输入对应行动备考，或'过月'推进时间。考试月将自动出题。"
            return {"type": "备考", "narrative": menu, "harvest_tags": "备考", "energy_cost": 0, "player": player}

        # === 考试月：出题/答题 ===
        level_name, total_score = get_player_exam_level(player)
        question = get_exam_question(level_name)

        is_answer = len(user_input) > 10 and ("答" in user_input or "曰" in user_input or "论" in user_input)
        if not is_answer:
            energy_cost = 2
            check = action_energy_check(player, user_input, energy_cost)
            if not check['can_act']:
                return {"type": "科举", "narrative": check['reason'], "player": player}
            player['energy'] = check['new_energy']
            save_player(user_id, {'energy': player['energy']})
            return {
                "type": "科举", "exam_mode": "question", "question": question,
                "level": level_name, "total_score": total_score,
                "narrative": f"⚡ 科举月！\n【{question['topic']}】{question.get('title')}\n{question.get('background','')}",
                "harvest_tags": "获题", "energy_cost": energy_cost,
                "guide_line": "→ 输入你的策论作答，或'过月'跳过。", "player": player}

        # 作答评分
        energy_cost = 5
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "科举", "narrative": check['reason'], "player": player}

        result = grade_answer(player, question, user_input)
        score = result['score']
        player['energy'] = check['new_energy']

        # 更新科举积分
        old_total = player.get('exam_total_score', 0)
        player['exam_total_score'] = old_total + score
        new_level, _ = get_player_exam_level(player)

        # 名望变化
        prestige_update = score // 10
        save_player(user_id, {
            'energy': player['energy'],
            'exam_total_score': player['exam_total_score'],
            'prestige': player.get('prestige', '默默无闻'),
        })

        narrative = f"【科举·{question.get('topic', '')}】{question.get('title', '')}\n\n"
        narrative += f"得分：{score}分 | 文采{result['literary']} 逻辑{result['logic']} 见识{result['insight']}\n"
        narrative += f"评语：{result['comment']}\n"
        narrative += f"累计积分：{old_total}→{player['exam_total_score']}"
        if new_level != level_name:
            narrative += f"\n\n⚡ 晋升！科举等级：{level_name}→{new_level}"

        return {
            "type": "科举",
            "narrative": narrative,
            "player": player,
            "energy_cost": energy_cost,
            "exam_result": result,
            "level_name": new_level,
        }

    # 研发
    if action_type == "研发":
        from .tech_tree import get_tech_status, can_research_tech, research_tech
        energy_cost = ENERGY_COST.get("研发", 6)

        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "研发", "narrative": check['reason'], "player": player}

        tech_status = get_tech_status(user_id)

        # 查找玩家想研发的科技
        target_tech = None
        for cat, techs in tech_status.items():
            if isinstance(techs, list):
                for t in techs:
                    if t['name'] in user_input:
                        target_tech = t
                        break
                if target_tech:
                    break

        if not target_tech:
            # 显示科技树
            player['energy'] = check['new_energy']
            save_player(user_id, {'energy': player['energy']})
            summary = tech_status.get('_summary', {})
            narrative = f"【科技研发总览】已完成{summary.get('researched', 0)}/{summary.get('total', 0)}\n输入'研发 具体科技名称'开始研发"
            return {
                "type": "研发",
                "narrative": narrative,
                "tech_status": tech_status,
                "player": player,
                "energy_cost": energy_cost,
            }

        # 执行研发
        if not can_research_tech(user_id, target_tech['name']):
            return {
                "type": "研发",
                "narrative": f"无法研发「{target_tech['name']}」：前置科技未完成。\n需要：{', '.join(target_tech.get('prerequisites', []))}",
                "player": player,
            }

        player['energy'] = check['new_energy']
        research_points = random.randint(15, 35)  # 一次研发投入的进度
        result = research_tech(user_id, target_tech['name'], research_points)

        if result.get('completed'):
            save_player(user_id, {'energy': player['energy']})
            narrative = f"【研发完成】{target_tech['name']}！\n{target_tech.get('desc', '')}\n效果：{target_tech.get('effects', {})}"
        else:
            save_player(user_id, {'energy': player['energy']})
            pct = f"{research_points}/{target_tech.get('cost', 100)}"
            narrative = f"【研发进行中】{target_tech['name']}\n进度：{result.get('progress', pct)}"

        return {
            "type": "研发",
            "narrative": narrative,
            "player": player,
            "energy_cost": energy_cost,
            "tech_status": get_tech_status(user_id),
        }

    # 情报打探
    if action_type == "情报":
        energy_cost = 4
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "情报", "narrative": check['reason'], "player": player}

        player['energy'] = check['new_energy']
        # 确定情报分类
        cat = "军事"
        if any(w in user_input for w in ["朝", "官", "政"]):
            cat = "政治"
        elif any(w in user_input for w in ["商", "价", "货", "买卖"]):
            cat = "商业"
        elif any(w in user_input for w in ["人", "私", "秘密"]):
            cat = "私人"

        # 生成情报
        intel = classify_intel(generate_intel(cat), cat)
        intel["获取时间"] = player.get("current_time", "宣和二年正月")
        intel["来源渠道"] = "自行打探"
        add_intel(user_id, intel)

        save_player(user_id, {'energy': player['energy']})
        hint = RELIABILITY_GRADES.get(intel["可靠度"], {}).get("叙事暗示", "")
        narrative = f"【情报获取】{hint}：{intel['内容']}"
        return {
            "type": "情报",
            "narrative": narrative,
            "status_line": format_status_line(player, "情报"),
            "energy_cost": energy_cost,
            "player": player,
        }

    # 随从
    if action_type == "随从":
        energy_cost = 3
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "随从", "narrative": check['reason'], "player": player}

        player['energy'] = check['new_energy']
        followers = get_followers(user_id)
        cap = get_follower_cap(player.get('power', '微末'))

        # 招募意图
        if any(w in user_input for w in ["招募", "招揽", "雇佣"]):
            if len(followers) >= cap:
                return {"type": "随从", "narrative": f"随从已达上限（{cap}人），无法再招募", "player": player}
            f_type = "仆役"
            if any(w in user_input for w in ["护卫", "保镖"]):
                f_type = "护卫"
            elif any(w in user_input for w in ["谋士", "军师", "幕僚"]):
                f_type = "谋士"
            elif any(w in user_input for w in ["商帮", "掌柜"]):
                f_type = "商帮"
            f_name = random.choice(["张三", "李四", "王五", "赵六", "周七"])
            new_f = create_follower(f_name, f_type, "雇佣")
            from .db import get_db, DATABASE_URL
            conn = get_db()
            ph = '%s' if DATABASE_URL else '?'
            conn.execute(f"INSERT INTO followers (user_id, name, f_type, loyalty, skill, salary) VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
                        (user_id, new_f['name'], new_f['f_type'], new_f['loyalty'], new_f['skill'], 5))
            conn.commit()
            conn.close()
            save_player(user_id, {'energy': player['energy']})
            return {"type": "随从", "narrative": f"招募了{f_type}「{f_name}」（忠诚：{new_f['loyalty']}）", "player": player}

        # 使用随从
        if followers:
            f = followers[0]
            action = "打探消息"
            if any(w in user_input for w in ["跑腿", "传信", "送信"]):
                action = "跑腿传信"
            elif any(w in user_input for w in ["护卫", "保护"]):
                action = "护卫随行"
            elif any(w in user_input for w in ["经营", "管账"]):
                action = "辅助经营"
            effect, cost, rate = use_follower_action(f, action)
            save_player(user_id, {'energy': player['energy']})
            return {"type": "随从", "narrative": f"「{f['name']}」{effect}", "player": player}

        save_player(user_id, {'energy': player['energy']})
        return {"type": "随从", "narrative": "当前无随从可用。输入'招募 类型'来招揽。", "player": player}

    # 物品使用
    if action_type == "物品":
        energy_cost = 2
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "物品", "narrative": check['reason'], "player": player}

        player['energy'] = check['new_energy']
        items = get_items(user_id)

        # 赠礼
        if any(w in user_input for w in ["赠", "送", "给"]) and items:
            item = items[0]
            npcs = get_npcs(user_id)
            target_npc = None
            if npcs:
                target_npc = npcs[0]
            if target_npc:
                match, bond_delta, desc = evaluate_gift_match(
                    item.get('category', ''), 
                    random.randint(3, 30),
                    target_npc.get('npc_identity', ''),
                    target_npc.get('npc_power', '微末'),
                    target_npc.get('npc_greed', '中')
                )
                new_bond = level_shift(target_npc.get('bond', '寻常'), BOND_ORDER, bond_delta // 2)
                update_npc(user_id, target_npc['name'], {'bond': new_bond})
                save_player(user_id, {'energy': player['energy']})
                return {"type": "物品", "narrative": f"将「{item.get('name', '礼物')}」赠予{target_npc['name']}——{desc}（好感变化：{bond_delta:+d}）", "player": player}

        save_player(user_id, {'energy': player['energy']})
        return {"type": "物品", "narrative": f"当前持有{len(items)}件物品。输入'赠给[NPC名] [物品名]'来赠礼。", "player": player}

    # 风月（完整版）
    if action_type == "风月":
        energy_cost = 3
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "风月", "narrative": check['reason'], "player": player}

        player['energy'] = check['new_energy']
        venue = "樊楼"
        interaction = "打茶围"
        if any(w in user_input for w in ["勾栏", "瓦舍"]):
            venue = "勾栏行院"
        elif any(w in user_input for w in ["茶坊", "茶肆"]):
            venue = "茶坊"
        if any(w in user_input for w in ["重金", "包", "包养"]):
            interaction = "重金包妓"
        elif any(w in user_input for w in ["赏曲", "听曲", "不涉"]):
            interaction = "只赏曲不涉风月"
        elif any(w in user_input for w in ["打探", "套话"]):
            interaction = "暗中打探"
        elif any(w in user_input for w in ["品茗", "论道"]):
            interaction = "品茗论道"

        result = visit_pleasure(player, venue, interaction)
        save_player(user_id, {'energy': player['energy']})

        # 情报获取
        if result['intel_gain'] > 0:
            from .intelligence import generate_intel, classify_intel
            intel = classify_intel(generate_intel("私人"), "私人")
            intel["获取时间"] = player.get("current_time", "")
            intel["来源渠道"] = f"{venue}{interaction}"
            from .db import add_intel
            add_intel(user_id, intel)

        narrative = result['description']
        return {"type": "风月", "narrative": narrative, "player": player, "energy_cost": energy_cost}

    # 后宫（完整版）
    if action_type == "后宫":
        if player.get("identity") != "妃嫔":
            return {"type": "后宫", "narrative": "后宫宫斗仅限妃嫔身份。", "player": player}

        # 解析具体行动
        act_type = "妆扮候驾"
        for key in FULL_HAREM_ACTIONS:
            if key in user_input:
                act_type = key
                break

        energy_cost = FULL_HAREM_ACTIONS[act_type]["精耗"]
        check = action_energy_check(player, user_input, energy_cost)
        if not check['can_act']:
            return {"type": "后宫", "narrative": check['reason'], "player": player}

        player['energy'] = check['new_energy']
        current_favor = int(player.get("favor", 50))
        rank_idx = int(player.get("harem_rank_index", 0))

        result = do_harem_action(player, act_type, current_favor, rank_idx)

        if "error" in result:
            return {"type": "后宫", "narrative": result["error"], "player": player}

        # 保存恩宠和位份
        save_data = {
            'energy': player['energy'],
            'favor': result['new_favor'],
            'harem_rank_index': result['rank_index'],
        }
        save_player(user_id, save_data)
        player.update(save_data)

        narrative = f"后宫之中，{result['action']}。{result['fav_desc']}。"
        if result.get('rank_up'):
            narrative += f"\n✨ 晋位「{result['current_rank']}」！"
        if result.get('served_tonight'):
            narrative += "\n是夜官家临幸。"
            # 妊娠检定
            children = get_children(player)
            age = int(player.get('age', 20))
            preg_result, preg_months, preg_desc = pregnancy_check(age, result['new_level'])
            if preg_result == "怀孕":
                player["is_pregnant"] = True
                player["pregnancy_months"] = 0
                narrative += f"\n{preg_desc}"

        return {"type": "后宫", "narrative": narrative, "player": player, "energy_cost": energy_cost}

    # 通用行动处理
    energy_cost = ENERGY_COST.get(action_type, 3)
    check = action_energy_check(player, user_input, energy_cost)
    if not check['can_act']:
        return {
            "type": action_type,
            "narrative": check['reason'],
            "status_line": format_status_line(player, action_type),
            "energy_cost": 0,
            "player": player,
        }

    # 确定关联属性
    attr_map = {
        "功名": "intelligence", "经营": "intelligence",
        "战斗": "military", "社交": "charm",
        "风月": "charm", "犯罪": "intelligence",
    }
    attr_key = attr_map.get(action_type, "intelligence")
    player_attr = player.get(attr_key, '平庸')

    # 确定关联技能
    skill_map = {
        "功名": "经义", "经营": "商道",
        "战斗": "兵学", "犯罪": "律法",
    }
    skill_name = skill_map.get(action_type, "")
    skill_level = '未涉猎'
    if skill_name:
        skills = get_skills(user_id)
        for s in skills:
            if s['skill_name'] == skill_name:
                skill_level = s['level']
                break

    # 成功率判定
    result = action_success_rate(player_attr, skill_level)
    # 性格维度修正
    if action_type in ("社交", "功名"):
        person_bonus = get_personality_bonus(player, "yili_actions", action_type)
        if person_bonus > 0:
            result['success'] = True
        elif person_bonus < 0 and result['success']:
            result['success'] = random.random() > 0.3
    elif action_type in ("战斗", "犯罪"):
        person_bonus = get_personality_bonus(player, "danyong_actions", action_type)
        if person_bonus > 0:
            result['success'] = True
    success = result['success']

    # 处理特定行动类型
    bond_change = None
    exposure_change = None
    combat_result = None
    npc_decision = None

    if action_type == "社交":
        # 找NPC
        npcs = get_npcs(user_id)
        target_npc = None
        for n in npcs:
            if n['name'] in user_input:
                target_npc = n
                break
        if target_npc:
            bond_change = action_bond_change(target_npc['bond'], '帮助')
            if bond_change['bond_changed']:
                update_npc(target_npc['id'], {'bond': bond_change['new_bond'], 'months_no_interact': 0})
            npc_decision = action_npc_decision(
                target_npc.get('npc_loyalty', '中'),
                target_npc.get('npc_greed', '中'),
                target_npc.get('npc_malice', '中'),
                target_npc.get('npc_power', '微末'),
                player.get('power', '微末'),
                target_npc.get('bond', '寻常'),
            )
        else:
            target_npc = None

    if action_type in ["犯罪", "风月"]:
        crime_map = {"犯罪": "走私"}
        for ct in ["通奸", "走私", "贪污", "谋杀", "伪造"]:
            if ct in user_input:
                crime_map = {"犯罪": ct}
                break
        exposure_change = action_exposure_risk(
            player.get('exposure_risk', '安全'),
            crime_map.get("犯罪", "走私")
        )

    if action_type == "战斗":
        enemy_troops = random.randint(50, 500)
        player_troops = int(player.get('troops', 100))
        combat_result = combat_resolve(
            player.get('military', '平庸'),
            max(player_troops, 50),
            enemy_troops,
            skill_level,
        )
        player['troops'] = combat_result['remaining_troops']
        if combat_result['loot_money'] > 0:
            player['money'] = float(player.get('money', 0)) + combat_result['loot_money']

        injury = combat_injury(combat_result['injury_risk'], player.get('military', '平庸'))
        if injury['injured']:
            health_status = json.loads(player.get('health_status', '[]'))
            health_status.append({
                "name": injury['injury_name'],
                "months_left": injury['recovery_months']
            })
            player['health_status'] = json.dumps(health_status, ensure_ascii=False)
            player['health_trend'] = '趋降'

    # 更新玩家状态
    player['energy'] = check['new_energy']
    player['month_days_elapsed'] = int(player.get('month_days_elapsed', 0)) + random.randint(1, 5)

    if exposure_change and exposure_change['risk_changed']:
        player['exposure_risk'] = exposure_change['new_risk']
        if action_type == "犯罪":
            player['crime_this_month'] = int(player.get('crime_this_month', 0)) + 1

    # 性格行为累计
    if any(w in user_input for w in ["仗义", "行善", "救人", "慷慨"]):
        player['yili_actions'] = int(player.get('yili_actions', 0)) + 1
    if any(w in user_input for w in ["强硬", "刚直", "不屈"]):
        player['gangrou_actions'] = int(player.get('gangrou_actions', 0)) + 1
    if any(w in user_input for w in ["宽恕", "包容", "大度"]):
        player['kuanxia_actions'] = int(player.get('kuanxia_actions', 0)) + 1
    if any(w in user_input for w in ["冒险", "勇猛", "冲锋"]):
        player['danyong_actions'] = int(player.get('danyong_actions', 0)) + 1

    save_player(user_id, player)

    # 生成叙事
    npc_name = ""
    if action_type == "社交" and bond_change:
        npcs = get_npcs(user_id)
        if npcs:
            npc_name = npcs[0]['name']

    detail = ""
    if combat_result:
        detail = f"战果：{combat_result['result']}，伤亡{combat_result['casualties']}人"
    elif bond_change and bond_change['bond_changed']:
        detail = f"好感{bond_change['old_bond']}→{bond_change['new_bond']}"
    elif exposure_change and exposure_change['risk_changed']:
        detail = "似乎有人在背后议论什么"

    narrative = generate_narrative(action_type, success, detail=detail, npc=npc_name, action=user_input[:20], player=player)

    # 收获标签
    harvest_tags = []
    if success:
        tag_map = {
            "功名": "[学识][文名↑]", "经营": "[财富][商道微悟]",
            "战斗": "[武名↑][军功]", "社交": "[人脉][好感↑]",
            "犯罪": "[隐秘][财富]", "风月": "[人脉][情报]",
            "日常": "[阅历][经验]",
            "科举": "[学识][文名↑]",
            "研发": "[科技][智慧增长]",
        }
        harvest_tags = [tag_map.get(action_type, "[经验]")]
    else:
        harvest_tags = ["[教训]", "[警觉↑]"]

    status_line = format_status_line(player, action_type)

    # 检查是否需要过月
    need_month_settle = player['energy'] <= 0 or player['month_days_elapsed'] >= 30

    cost_line, formatted_status_line, guide_line = build_output(
        player, narrative, action_type, energy_cost,
        " ".join(harvest_tags), combat_result
    )

    return {
        "type": action_type,
        "narrative": narrative,
        "cost_line": cost_line,
        "status_line": formatted_status_line,
        "guide_line": guide_line,
        "energy_cost": energy_cost,
        "harvest_tags": " ".join(harvest_tags),
        "player": player,
        "need_month_settle": need_month_settle,
        "combat_result": combat_result,
        "bond_change": bond_change,
        "exposure_change": exposure_change,
        "success": success,
        "success_level": result['success_level'],
    }
