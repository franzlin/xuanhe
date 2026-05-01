"""
《宣和二年》水浒金瓶梅深度剧情网 (§十九)
动态关系网 + 地点生态 + 道德抉择池
"""
import random
import json

# ============================
# IP驱动逻辑
# ============================
IP_INFO = {
    "水浒": {
        "核心驱动力": "义气/招安/替天行道",
        "干预维度": ["结交头领", "干预劫掠", "影响招安时机", "选择官府/梁山立场"],
        "后果": {
            "背叛": "被江湖除名，遭梁山追杀",
            "投靠": "获梁山庇护，江湖名↑↑",
            "中立": "两不相帮，静观其变",
        },
    },
    "金瓶梅": {
        "核心驱动力": "欲望/商贾/宅门秘辛",
        "干预维度": ["结交西门庆", "介入商业竞争", "宅门站队", "青楼打茶围"],
        "后果": {
            "介入": "卷入毒杀案/商号破产风险",
            "旁观": "获知市井秘闻但不得罪人",
        },
    },
}

# ============================
# 地点生态
# ============================
LOCATION_ECOLOGY = {
    "梁山泊": {
        "核心机制": "聚义厅议事/劫掠分赃/招安分歧",
        "NPC": ["宋江", "吴用", "卢俊义", "李逵", "林冲", "武松"],
        "指令": ["聚义厅请令", "劫生辰纲", "劝宋江拒招安", "结识好汉", "打探官军动向"],
    },
    "清河县": {
        "核心机制": "商号经营/宅门站队/市井流言",
        "NPC": ["西门庆", "潘金莲", "武大郎", "王婆"],
        "指令": ["拜访生药铺", "打点县衙", "探听武家秘事", "结交西门大官人"],
    },
    "汴京瓦舍": {
        "核心机制": "听曲打茶围/情报交换/露水情缘",
        "NPC": ["李师师", "行院名妓", "说书人"],
        "指令": ["樊楼宴客", "行院打茶围", "听书探风声", "结识李师师"],
    },
}

# ============================
# 道德抉择池
# ============================
MORAL_CHOICES = [
    {
        "场景": "晁盖劫生辰纲事发",
        "触发条件": "江湖名≥小有名气",
        "选项": [
            {"选": "报官邀功", "效果": "官声↑、江湖名↓、获赏金"},
            {"选": "暗中放走", "效果": "江湖名↑、官声↓、梁山好感↑"},
            {"选": "索要封口费", "效果": "金钱↑、警惕↑、贪欲↑"},
        ],
    },
    {
        "场景": "潘金莲递毒酒",
        "触发条件": "在清河县+与西门庆有往来",
        "选项": [
            {"选": "揭发", "效果": "民望↑、西门庆敌对"},
            {"选": "默许", "效果": "阴毒↑、丑闻风险、获西门庆把柄"},
            {"选": "分赃", "效果": "金钱↑、把柄留、阴毒↑↑"},
        ],
    },
    {
        "场景": "梁山招安诏书到",
        "触发条件": "江湖名≥小有名气或与梁山有往来",
        "选项": [
            {"选": "力主受招", "效果": "帝党↑、江湖名↓、获朝廷封赏"},
            {"选": "劝其割据", "效果": "江湖名↑↑、朝廷通缉"},
            {"选": "置身事外", "效果": "中立保全、两边不得罪"},
        ],
    },
    {
        "场景": "西门庆邀入股",
        "触发条件": "在清河县+商道≥初窥门径",
        "选项": [
            {"选": "重金入股", "效果": "金-50贯、月分红、获商业情报"},
            {"选": "婉拒", "效果": "安全、错过商机"},
            {"选": "假意入股暗查账", "效果": "智力↑、获西门庆贪墨证据"},
        ],
    },
    {
        "场景": "梁山好汉落难求助",
        "触发条件": "随机(月概率0.15)+江湖名≥默默无闻",
        "选项": [
            {"选": "仗义收留", "效果": "江湖名↑、梁山好感↑↑、风险↑"},
            {"选": "资助盘缠", "效果": "金-10贯、江湖名微↑"},
            {"选": "拒之门外", "效果": "安全、江湖名↓"},
        ],
    },
]


def should_trigger_ip_event(player, location, month_count=1):
    """判断是否触发IP事件"""
    if location in ("梁山泊", "水泊梁山"):
        return "水浒", "梁山泊", 0.3
    if location in ("清河县", "阳谷县"):
        return "金瓶梅", "清河县", 0.25
    if location in ("东京开封府", "汴京"):
        return "瓦舍", "汴京瓦舍", 0.15
    return None, None, 0


def get_moral_choice(player):
    """获取一个道德抉择场景"""
    available = []
    for choice in MORAL_CHOICES:
        cond = choice.get("触发条件", "")
        if "江湖名" in cond:
            prest = player.get("prestige_jianghu", "默默无闻")
            if "小有名气" in cond and prest not in ("默默无闻",):
                available.append(choice)
        elif "清河县" in cond:
            if player.get("location", "") in ("清河县", "阳谷县"):
                available.append(choice)
        else:
            available.append(choice)

    if not available:
        return MORAL_CHOICES[-1]
    return random.choice(available)


def execute_location_action(location, action, player):
    """执行地点专属行动"""
    ecology = LOCATION_ECOLOGY.get(location)
    if not ecology:
        return {"error": "未知地点"}

    if action not in ecology["指令"]:
        return {"error": f"{location}不支持此行动，可用：{', '.join(ecology['指令'])}"}

    # 基础效果
    result = {
        "location": location,
        "action": action,
        "cost": 3,
        "description": f"在{location}{action}",
    }

    if "聚义厅" in action:
        result["description"] = "聚义厅上，好汉分列两行。宋江起身让座：「贤弟请了！」"
        result["江湖名变化"] = 1
    elif "劫生辰纲" in action:
        result["description"] = "月黑风高，一队押运车队缓缓行来……"
        result["cost"] = 8
        result["金钱变化"] = random.randint(20, 100)
        result["风险"] = "朝廷追查"
    elif "招安" in action:
        result["description"] = "宋江沉吟半晌：「招安……或是割据一方……贤弟怎么看？」"
    elif "西门" in action or "生药铺" in action:
        result["description"] = "西门庆拱手迎出：「贵客登门，快请上座！」"
        result["cost"] = 2
    elif "武家" in action:
        result["description"] = "王婆挤眉弄眼：「大官人想知道什么？」"
        result["情报"] = "可信"
    elif "李师师" in action:
        result["description"] = "李师师轻拨琴弦：「官人今日想听什么曲？」"
        result["cost"] = 5
        result["关系"] = "初识李师师"
    elif "听书" in action:
        result["description"] = "说书人醒木一拍：「话说宣和二年……」"
        result["情报"] = "传闻"

    return result


def get_shuihuo_npcs_for_location(location):
    """获取某地点的水浒金瓶梅NPC"""
    ecology = LOCATION_ECOLOGY.get(location)
    if ecology:
        return ecology.get("NPC", [])
    return []


def create_shuihuo_npc(name, location_tag):
    """创建水浒金瓶梅NPC数据"""
    npc_db = {
        "宋江": {"名号": "及时雨·梁山首领", "性格": "外忠内谋", "势力": "梁山"},
        "吴用": {"名号": "智多星·军师", "性格": "深沉多智", "势力": "梁山"},
        "李逵": {"名号": "黑旋风", "性格": "莽撞忠勇", "势力": "梁山"},
        "西门庆": {"名号": "生药铺东家", "性格": "好色贪财", "势力": "市井"},
        "潘金莲": {"名号": "武大之妻", "性格": "风情不甘", "势力": "市井"},
        "李师师": {"名号": "汴京名妓", "性格": "才情高傲", "势力": "瓦舍"},
    }
    info = npc_db.get(name, {"名号": "", "性格": "", "势力": ""})
    return {
        "name": name,
        "tags": ["水浒" if info["势力"] == "梁山" else "金瓶梅" if info["势力"] == "市井" else "瓦舍"],
        "note": info.get("名号", ""),
        "npc_personality": info.get("性格", ""),
        "npc_faction": "宋",
        "location": location_tag,
    }
