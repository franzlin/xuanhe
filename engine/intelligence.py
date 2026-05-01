"""
《宣和二年》情报系统 (Intelligence System)
对齐《核心机制》§二十七

设计原则：
- 情报在游戏中无处不在，为行动提供修正加成
- 四类情报各有不同获取难度和时效
- 三档可靠度通过叙事暗示（不暴露数值）
- 假情报来自敌对NPC或不可靠渠道
"""
import json
import random
import time


# ============================
# 情报分类与时效
# ============================

INTEL_CATEGORIES = {
    "军事": {
        "获取难度": "高",
        "默认时效_月": 2,
        "过期后果": "敌情已变，依此行动→误判",
        "示例": "金军在燕京集结，月内恐南侵",
    },
    "政治": {
        "获取难度": "中",
        "默认时效_月": 2,
        "过期后果": "派系格局已变，依此站队→选错",
        "示例": "蔡京近日将上书罢免李纲",
    },
    "商业": {
        "获取难度": "低",
        "默认时效_月": 1,
        "过期后果": "行情已变，依此囤货→亏损",
        "示例": "东南丝价下月将涨三成",
    },
    "私人": {
        "获取难度": "中",
        "默认时效_月": 4,
        "过期后果": "秘密泄露或对方已察觉",
        "示例": "西门庆正密谋毒杀武大郎",
    },
}

# 可靠度3档
RELIABILITY_GRADES = {
    "确凿": {"失真概率": 0.10, "叙事暗示": "千真万确", "加成": 1.0},
    "可信": {"失真概率": 0.25, "叙事暗示": "据可靠消息", "加成": 0.7},
    "传闻": {"失真概率": 0.50, "叙事暗示": "坊间传言", "加成": 0.3},
}

# 获取渠道与成本
INTEL_CHANNELS = {
    "人际打听": {
        "条件": "好感≥友善的NPC",
        "精力消耗": 3,
        "金钱消耗": 0,
        "基础成功率": 0.7,
        "情报品质": "可信",
        "风险": "暴露询问意图→警惕↑",
    },
    "市井打探": {
        "条件": "魅力≥普通",
        "精力消耗": 4,
        "金钱消耗": 1.0,
        "基础成功率": 0.5,
        "情报品质": "传闻",
        "风险": "假情报概率高",
    },
    "暗桩眼线": {
        "条件": "权力值≥小吏",
        "精力消耗": 4,
        "金钱消耗": 5.0,
        "基础成功率": 0.75,
        "情报品质": "可信",
        "风险": "暗桩被收买→反送假情报",
    },
    "皇城司/密探": {
        "条件": "权力值≥朝堂",
        "精力消耗": 5,
        "金钱消耗": 10.0,
        "基础成功率": 0.9,
        "情报品质": "确凿",
        "风险": "被发现→帝党好感↓",
    },
    "自行侦察": {
        "条件": "警惕≥中",
        "精力消耗": 5,
        "金钱消耗": 0,
        "基础成功率": 0.5,
        "情报品质": "可信",
        "风险": "被反侦察→暴露意图",
    },
}

# 情报用于行动修正
INTEL_USAGE_BONUS = {
    "游说说服": "已知对方弱点→成功率+1级",
    "商业决策": "已知行情走向→盈亏判定+1级",
    "军事行动": "已知敌情→布阵针对性↑，伤亡率↓1档",
    "政治站队": "已知派系动向→选边成功率↑",
    "构陷反制": "已知对方把柄→构陷成功率+1级",
}

# 情报内容模板池（按分类）
INTEL_TEMPLATES = {
    "军事": [
        "{势力}军在{地点}集结，月内恐有军事行动",
        "{势力}粮草不济，士卒逃亡日增",
        "边关榷场关闭在即，{势力}备战迹象明显",
        "{势力}新铸火器已运抵前线",
        "探子回报{地点}城防空虚，守军不足{数量}",
        "{将领}与{将领}不和，军中暗流汹涌",
    ],
    "政治": [
        "{权臣}近日将上奏弹劾{目标}",
        "台谏闻风而动，{事件}案即将重审",
        "宫内传出消息，官家有意召{人物}回京",
        "{派系}正拉拢{人物}，站队良机",
        "吏部注拟名单泄露，{官职}即将空缺",
        "朝议将讨论{政策}，各方势力蠢蠢欲动",
    ],
    "商业": [
        "{商品}受漕运阻滞，下月将涨价{幅度}",
        "{地点}新开榷场，{商品}供不应求",
        "花石纲加征{地点}商税，行商纷纷避走",
        "{产业}受盗匪侵扰，产量锐减{幅度}",
        "官府即将发包{工程}，商机巨大",
        "{地区}丰年，{商品}价格大跌至谷底",
    ],
    "私人": [
        "{人物}暗中与{人物}过从甚密",
        "{人物}有把柄落在{人物}手中",
        "{人物}家产来历不明，疑似贪墨",
        "{人物}与{人物}有旧怨，可资利用",
        "{人物}身患隐疾，求医于{医者}",
        "{人物}私生子养在{地点}，秘而不宣",
    ],
}


def generate_intel(category, player_faction="宋", player_location="东京开封府"):
    """根据分类生成一条情报内容"""
    import random

    templates = INTEL_TEMPLATES.get(category, INTEL_TEMPLATES["私人"])
    template = random.choice(templates)

    # 填充常见变量
    fillings = {
        "势力": random.choice(["金", "辽", "西夏", "蒙古", "方腊"]),
        "地点": random.choice(
            ["燕京", "太原", "杭州", "大名府", "洛阳", "应天府", "西夏兴庆府",
             player_location]
        ),
        "将领": random.choice(["种师道", "童贯", "宗泽", "韩世忠", "岳飞", "刘光世"]),
        "数量": random.choice(["三千", "五千", "一万"]),
        "权臣": random.choice(["蔡京", "童贯", "王黼", "李邦彦"]),
        "目标": random.choice(["李纲", "种师道", "张叔夜", "宗泽"]),
        "事件": random.choice(["花石纲", "方腊之乱", "西北边衅"]),
        "人物": random.choice(
            ["蔡京", "童贯", "李纲", "种师道", "高俅", "西门庆", "宋江", "张叔夜"]
        ),
        "派系": random.choice(["蔡党", "清流", "西军", "帝党"]),
        "官职": random.choice(["开封府推官", "殿中侍御史", "枢密副使"]),
        "政策": random.choice(["方田均税", "募役法", "保甲法"]),
        "商品": random.choice(["丝绸", "茶叶", "粮食", "铁器", "盐", "马匹"]),
        "幅度": random.choice(["两成", "三成", "一半", "一倍"]),
        "产业": random.choice(["织造", "漕运", "矿冶", "盐业"]),
        "工程": random.choice(["黄河堤防", "汴河疏浚", "城垣修缮"]),
        "地区": random.choice(["东南", "西北", "河北", "京东"]),
        "医者": random.choice(["安道全", "许叔微", "钱乙"]),
    }
    for key, val in fillings.items():
        template = template.replace(f"{{{key}}}", val, 1)

    return template


def classify_intel(intel_text, category):
    """为一条情报分配可靠度和时效"""
    reliability_map = {
        "确凿": random.random() < 0.3,
        "可信": random.random() < 0.5,
        "传闻": random.random() < 0.5,
    }
    # 更大概率是可信
    if random.random() < 0.5:
        reliability = "可信"
    elif random.random() < 0.7:
        reliability = "传闻"
    else:
        reliability = "确凿"

    # 时效（月）
    base_ttl = INTEL_CATEGORIES[category]["默认时效_月"]
    ttl_months = base_ttl + random.randint(-1, 2)

    return {
        "分类": category,
        "内容": intel_text,
        "可靠度": reliability,
        "失效月份": ttl_months,
        "获取时间": "",
        "来源渠道": "",
    }


def get_intel_reliability_bonus(reliability):
    """获取情报可靠度对应的行动修正加成"""
    return RELIABILITY_GRADES.get(reliability, RELIABILITY_GRADES["传闻"])["加成"]


def is_intel_expired(intel_record, current_month):
    """检查情报是否过期"""
    if not intel_record:
        return True
    acquired = intel_record.get("acquired_month", "")
    ttl = intel_record.get("ttl_months", 1)
    if not acquired:
        return False
    # 简单比较：如果时效已过
    try:
        # acquired_month格式: "宣和二年正月"
        months_order = [
            "正月", "二月", "三月", "四月", "五月", "六月",
            "七月", "八月", "九月", "十月", "十一月", "十二月"
        ]
        # 解析当前月
        acq_parts = acquired.replace("宣和二年", "").replace("宣和三年", "").replace("宣和四年", "")
        cur_parts = current_month.replace("宣和二年", "").replace("宣和三年", "").replace("宣和四年", "")

        acq_year = 2 if "宣和二年" in acquired else (3 if "宣和三年" in acquired else 4)
        cur_year = 2 if "宣和二年" in current_month else (3 if "宣和三年" in current_month else 4)

        acq_idx = months_order.index(acq_parts) if acq_parts in months_order else 0
        cur_idx = months_order.index(cur_parts) if cur_parts in months_order else 0

        total_months_passed = (cur_year - acq_year) * 12 + (cur_idx - acq_idx)
        return total_months_passed > ttl
    except Exception:
        return False


def generate_rumor_or_intel(is_hostile=False, player_intelligence="平庸"):
    """生成一条随机传闻或情报（可来自敌对NPC）"""
    category = random.choice(list(INTEL_CATEGORIES.keys()))
    intel_text = generate_intel(category)

    # 敌对NPC提供假情报的概率
    if is_hostile:
        fake_prob = 0.6
        if player_intelligence in ("优良", "卓越"):
            fake_prob = 0.3
        if random.random() < fake_prob:
            # 标记为假情报
            return {
                "分类": category,
                "内容": intel_text,
                "可靠度": "传闻",
                "失真概率": 0.8,
                "来源": "敌对NPC",
                "可疑": True,
            }

    reliability = "可信" if not is_hostile else "传闻"
    return {
        "分类": category,
        "内容": intel_text,
        "可靠度": reliability,
        "失真概率": RELIABILITY_GRADES[reliability]["失真概率"],
        "来源": "敌对NPC" if is_hostile else "常规渠道",
        "可疑": is_hostile,
    }
