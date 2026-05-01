"""
《宣和二年》书信系统 (Letter System)
对齐《核心机制》§三十三

设计原则：
- NPC主动来信，触发条件由事件/关系/时间驱动
- 四种书信类型各有不同触发条件和频率
- 时间延迟基于距离（同城→跨路→边境）
- 书信有截获/伪造/泄密风险
"""
import random
import json


# ============================
# 书信类型与触发
# ============================

LETTER_TYPES = {
    "情势急信": {
        "触发条件": ["NPC遭遇重大变故", "发现阴谋", "被贬/被围", "紧急求援"],
        "频率上限": "不限（事件驱动）",
        "叙事基调": "急促焦灼",
        "示例开头": ["十万火急！", "事急，不及寒暄", "望君速览——"],
    },
    "日常问候": {
        "触发条件": ["好感≥友善的NPC", "异地超过3月", "过节/生辰"],
        "频率上限": "每季≤1封/人",
        "叙事基调": "温和平实",
        "示例开头": ["见字如面", "别来无恙？", "秋风渐起，念及故人——"],
    },
    "家族家书": {
        "触发条件": ["有家族成员在异地", "宗族事务", "父母催婚/催归"],
        "频率上限": "每月≤1封",
        "叙事基调": "家常唠叨",
        "示例开头": ["吾儿亲启", "族中诸事安好", "家中老母念你——"],
    },
    "求援信": {
        "触发条件": ["好感≥友善的NPC遭遇困境", "缺钱/被欺/兵乱/病危"],
        "频率上限": "不限（事件驱动）",
        "叙事基调": "恳切求助",
        "示例开头": ["万望援手", "走投无路，唯君可托", "若蒙相助——"],
    },
}

# 时间延迟（基于距离）
TIME_DELAY = {
    "同城": {"普通": "1日", "加急": "当日"},
    "同路（≤500里）": {"普通": "3~5日", "加急": "1~2日"},
    "跨路（>500里）": {"普通": "10~20日", "加急": "5~8日"},
    "边境/敌境": {"普通": "20~30日", "加急": "不保证送达"},
}

# 书信风险
LETTER_RISKS = {
    "截获": {
        "触发条件": "敌对势力+书信途经其控制区",
        "后果": "情报泄露，暴露风险+10~20",
        "概率": 0.25,
    },
    "伪造": {
        "触发条件": "对方百工≥初窥门径+智力≥优良",
        "后果": "假信误导玩家行动",
        "概率": 0.08,
    },
    "泄密": {
        "触发条件": "送信人忠诚低/被收买",
        "后果": "书信内容被第三者知晓",
        "概率": 0.15,
    },
}

# 书信模板池（按类型和情境）
LETTER_TEMPLATES = {
    "情势急信": {
        "被贬": [
            "忽遭台谏弹劾，圣上震怒。某已被贬逐{地点}，启程在即。朝中诸公唯恐牵连，无人敢送。唯望君知。",
        ],
        "发现阴谋": [
            "近日察得{人物}与{人物}暗通款曲，似有大谋。细节不便笔述，但此事关乎存亡。君宜早做准备。",
        ],
        "兵临城下": [
            "{势力}兵锋已至{地点}城下，围城{数量}重。城中粮草仅支半月。若援军不至，城破只在旦夕。",
        ],
        "病危": [
            "某旧疾复发，医者言凶多吉少。唯有一事挂念——{事件}。此事若不办妥，死不瞑目。",
        ],
        "告急": [
            "{事件}事发突然，蔡太师已下令彻查。某处境危殆，望君设法周旋。",
        ],
    },
    "日常问候": {
        "异地友": [
            "自{地点}一别，倏忽已{时间}。{地点}风物虽好，终不及故土。近日{事件}，更念与君把酒之日。",
            "得君信甚慰。{地点}一切安好，唯公务冗杂，每思退隐。京城若有新闻，万望告知。",
        ],
        "过节": [
            "中秋将至，月圆人未圆。忆昔年同游{地点}，不觉潸然。附赠{礼物}，聊表心意。",
            "岁末除夕，阖家团聚。独缺君一人，举杯遥祝安康。来年若得闲暇，望归乡一叙。",
        ],
    },
    "家族家书": {
        "催归": [
            "族中长辈年事已高，日日念你。族产事务日繁，若在外无大作为，不如归乡经营。",
            "你堂兄新得{官职}，族中已在{地点}购置田庄。你父嘱你趁年轻早做打算。",
        ],
        "婚事": [
            "{人物}家托媒提亲，对方门第清白，家资殷实。你若有意，可回信告知。",
            "你年岁渐长，姻缘不可再拖。{地点}{人物}有意与你结亲，速回信定夺。",
        ],
    },
    "求援信": {
        "缺钱": [
            "遭逢变故，家财散尽。店铺被迫盘出，子女嗷嗷待哺。若蒙借银{数量}贯，来日必加倍奉还。",
        ],
        "被欺": [
            "{人物}仗势欺人，霸占某田产/店铺。告官无门，对方与{派系}有旧。万望看在旧日情分施以援手。",
        ],
        "兵乱": [
            "{势力}兵过境，村寨被劫。某侥幸逃得性命，然家园尽毁。望君设法安置。",
        ],
        "救人": [
            "某因{事件}被下狱，罪在不赦。然实属冤枉——{详情}。若君能设法营救，某愿以死相报。",
        ],
    },
}


def generate_letter(letter_type, npc_name, npc_location="异地", context=None):
    """生成一封书信"""
    if letter_type not in LETTER_TYPES:
        return None

    type_info = LETTER_TYPES[letter_type]
    opening = random.choice(type_info["示例开头"])
    tone = type_info["叙事基调"]

    # 选择模板
    templates = LETTER_TEMPLATES.get(letter_type, {})
    if not templates:
        return None

    # 选一个情境
    if context and context in templates:
        scenario = context
    else:
        scenario = random.choice(list(templates.keys()))

    template = random.choice(templates[scenario])

    # 填充变量
    fillings = {
        "地点": npc_location,
        "时间": random.choice(["三月", "半载", "一年有余"]),
        "事件": random.choice(["花石纲骚动", "西军调防", "蔡太师新政", "边境告急"]),
        "人物": random.choice(["蔡京", "童贯", "李纲", "种师道", "高俅", "西门庆"]),
        "势力": random.choice(["金", "辽", "方腊", "西夏"]),
        "数量": random.choice(["五百", "三千", "一万"]),
        "官职": random.choice(["知州", "通判", "提举常平", "枢密副使"]),
        "礼物": random.choice(["蜀锦一匹", "建茶二两", "端砚一方", "龙泉剑一柄"]),
        "派系": random.choice(["蔡党", "清流", "西军"]),
        "详情": "某某某之事",
    }
    for key, val in fillings.items():
        template = template.replace(f"{{{key}}}", val, 1)

    letter = f"【{npc_name}来信】\n{opening}\n\n{template}\n\n——{npc_name} 于{npc_location}"
    return {
        "类型": letter_type,
        "发信人": npc_name,
        "发信地": npc_location,
        "内容": letter,
        "情境": scenario,
        "基调": tone,
    }


def should_send_letter(npc, player_location="东京开封府", month_count=1):
    """
    判断NPC是否应该发信
    返回: letter_type 或 None
    """
    bond = npc.get("bond", "寻常")
    npc_location = npc.get("npc_location", "")

    # 同城不发信
    if npc_location == player_location:
        return None

    bond_order = ["仇视", "疏远", "寻常", "友善", "至交"]
    try:
        bond_idx = bond_order.index(bond)
    except ValueError:
        bond_idx = 2

    # 好感太低不发信
    if bond_idx < 2:
        return None

    # 情势急信（事件驱动，概率低但无条件限制）
    if npc.get("health") in ("重病", "濒危") or npc.get("grudge_level") in ("深仇",):
        if random.random() < 0.4:
            return "情势急信"

    # 求援信
    if npc.get("health") in ("微恙", "伤病") and bond_idx >= 3:
        if random.random() < 0.2:
            return "求援信"

    # 日常问候（每季度限1次）
    if bond_idx >= 3 and month_count >= 3:
        return "日常问候"

    # 家族家书
    if npc.get("tags") and ("亲属" in str(npc.get("tags", "")) or "家族" in str(npc.get("tags", ""))):
        return "家族家书"

    return None


def get_travel_time(sender_location, player_location):
    """计算书信传递时间"""
    # 简化：根据地点判断距离
    near_cities = {
        "东京开封府": ["洛阳", "应天府", "大名府"],
        "洛阳": ["东京开封府", "应天府"],
        "应天府": ["东京开封府", "洛阳"],
    }

    if sender_location == player_location:
        return "同城"
    elif sender_location in near_cities.get(player_location, []) or player_location in near_cities.get(sender_location, []):
        return "同路（≤500里）"
    elif sender_location in ("燕京", "太原", "杭州", "成都", "广州", "兴庆府"):
        return "跨路（>500里）"
    elif sender_location in ("会宁", "中京", "蒙古草原"):
        return "边境/敌境"
    return "同路（≤500里）"


def check_letter_risk(distance_level, sender_party="", player_party=""):
    """检查书信风险"""
    risk_found = None

    # 敌对势力截获
    if distance_level == "边境/敌境":
        if random.random() < LETTER_RISKS["截获"]["概率"] * 2:
            risk_found = {"类型": "截获", "后果": LETTER_RISKS["截获"]["后果"]}

    # 伪造风险
    if random.random() < LETTER_RISKS["伪造"]["概率"]:
        risk_found = {"类型": "伪造", "后果": LETTER_RISKS["伪造"]["后果"]}

    # 泄密
    if not risk_found and random.random() < LETTER_RISKS["泄密"]["概率"]:
        risk_found = {"类型": "泄密", "后果": LETTER_RISKS["泄密"]["后果"]}

    return risk_found


def handle_reply_command(user_input):
    """解析回信指令"""
    import re
    # 格式: 写信给[NPC名]: [内容]
    match = re.search(r"写信给(.+?)[：:](.+)", user_input)
    if match:
        npc_name = match.group(1).strip()
        content = match.group(2).strip()
        return npc_name, content
    return None, None


def format_letter_for_display(letter):
    """格式化书信以在游戏中显示"""
    if not letter:
        return ""
    return letter.get("内容", "")
