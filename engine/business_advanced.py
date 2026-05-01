"""
《宣和二年》经营高级策略 (Business Advanced)
对齐《核心机制》§十

设计原则：
- 6项高级策略各有属性/技能门槛
- 环境联动：方腊→丝价、宋金→榷场、漕运→粮价
- 竞争NPC（西门庆等）可能反制
- 定性判定，不计算精确利润率
"""
import random


# ============================
# 高级经营策略
# ============================

ADVANCED_STRATEGIES = {
    "期货囤积": {
        "名称": "期货囤积",
        "属性要求": "智力≥普通",
        "技能要求": "商道≥登堂入室",
        "效果": "预判涨跌，低买高卖，单次利润↑↑",
        "风险": "判断失误→库存积压+资金链断裂",
        "消耗": "精4+金50贯起",
        "成功标志": "低价囤入→行情大涨→高价出手→暴利",
        "失败标志": "高价囤入→行情下跌→积压亏本",
    },
    "商战狙击": {
        "名称": "商战狙击",
        "属性要求": "智力≥优良+政治≥普通",
        "技能要求": "商道≥登堂入室",
        "效果": "收购原料/挖走掌柜/请官差查税，致对手破产",
        "风险": "失败则反噬；过度使用阴毒↑富名↓",
        "消耗": "精6+金100贯起",
        "成功标志": "对手倒闭，你的市场占有率↑↑",
        "失败标志": "对手反制，两败俱伤",
    },
    "政商绑定": {
        "名称": "政商绑定",
        "属性要求": "政治≥优良",
        "技能要求": "商道≥初窥门径",
        "效果": "结交官员获取盐引/茶引/军需订单",
        "风险": "派系失势→产业被抄；被绑上政治战车",
        "消耗": "精5+政治资源",
        "成功标志": "获盐引/茶引/军需→垄断利润",
        "失败标志": "官员倒台→被牵连清算",
    },
    "武装商队": {
        "名称": "武装商队",
        "属性要求": "军事≥普通",
        "技能要求": "商道+兵学≥初窥门径",
        "效果": "跨路贩运自带护卫，被劫率↓↓",
        "风险": "护卫月饷+武装投入，成本↑",
        "消耗": "精3+金30贯/月护卫",
        "成功标志": "商路通畅，跨路利润↑↑",
        "失败标志": "护卫溃败→货财两空",
    },
    "独家工艺": {
        "名称": "独家工艺",
        "属性要求": "智力≥优良",
        "技能要求": "百工≥登堂入室",
        "效果": "产品溢价+无法仿制，长期垄断利润",
        "风险": "技艺泄露/徒弟叛出→垄断瓦解",
        "消耗": "精5+研发成本",
        "成功标志": "独门产品→定价权→持续暴利",
        "失败标志": "技术被窃取→竞争对手仿制",
    },
    "军需供应": {
        "名称": "军需供应",
        "属性要求": "政治≥优良+权力值≥地方",
        "技能要求": "商道≥登堂入室",
        "效果": "以商养战，利润↑+功劳↑",
        "风险": "军队溃败→货款两空；军需延误→斩首",
        "消耗": "精6+金200贯起",
        "成功标志": "军需合同→稳定利润+军功记录",
        "失败标志": "军需延误→军法从事",
    },
}


# ============================
# 环境联动
# ============================

MARKET_EVENTS = {
    "方腊起事_东南": {
        "触发条件": "当前时间≥宣和二年十月",
        "影响": {
            "丝绸": {"趋势": "涨", "幅度": "三成", "原因": "东南商路中断"},
            "茶叶": {"趋势": "涨", "幅度": "两成", "原因": "产地遭兵灾"},
            "粮食": {"趋势": "涨", "幅度": "两成", "原因": "漕运受阻"},
        },
        "叙事": "方腊起事，东南大乱——丝绸茶叶断供，有存货者暴利。",
    },
    "宋金开战_边境": {
        "触发条件": "当前时间≥宣和三年",
        "影响": {
            "马匹": {"趋势": "断供", "幅度": "无从购入", "原因": "榷场关闭"},
            "铁器": {"趋势": "涨", "幅度": "三成", "原因": "军需激增"},
            "粮食": {"趋势": "涨", "幅度": "两成", "原因": "边境屯兵"},
            "药材": {"趋势": "涨", "幅度": "两成", "原因": "军营采购"},
        },
        "叙事": "宋金交兵，边境榷场关闭——铁/粮/药涨价，军需激增。",
    },
    "漕运阻滞_京城": {
        "触发条件": "随机（月概率0.2）",
        "影响": {
            "粮食": {"趋势": "涨", "幅度": "一档", "原因": "漕运不畅"},
            "酒肆成本": {"趋势": "涨", "幅度": "一档", "原因": "原料涨价"},
        },
        "叙事": "汴河淤塞，漕运阻滞——京城粮价上涨。",
    },
    "蔡党得势": {
        "触发条件": "蔡京在位",
        "影响": {
            "盐引茶引": {"趋势": "偏向", "幅度": "蔡党商人优先", "原因": "蔡京主政"},
            "非蔡党": {"趋势": "不利", "幅度": "常被查税", "原因": "打压异己"},
        },
        "叙事": "蔡太师当国，盐引茶引尽归蔡党——非依附者寸步难行。",
    },
}


def get_market_conditions(current_time):
    """获取当前市场环境"""
    conditions = []
    for event_name, info in MARKET_EVENTS.items():
        trigger = info.get("触发条件", "")
        if trigger.startswith("当前时间") and "宣和二年十月" in trigger:
            if "十月" in current_time or "十一月" in current_time or "十二月" in current_time or "宣和三年" in current_time:
                conditions.append(info)
        elif trigger.startswith("当前时间") and "宣和三年" in trigger:
            if "宣和三年" in current_time or "宣和四年" in current_time:
                conditions.append(info)
        elif trigger.startswith("随机"):
            if random.random() < 0.2:
                conditions.append(info)
        elif trigger == "蔡京在位":
            conditions.append(info)

    return conditions


def execute_advanced_strategy(strategy_name, player, business=None):
    """
    执行高级经营策略
    返回: (成功/失败, 效果描述, 金钱变化)
    """
    if strategy_name not in ADVANCED_STRATEGIES:
        return False, "未知策略", 0

    strat = ADVANCED_STRATEGIES[strategy_name]

    # 检查属性要求
    attr_req = strat["属性要求"]
    if "智力≥普通" in attr_req and player.get("intelligence", "平庸") not in ("普通", "优良", "卓越"):
        return False, f"{strategy_name}需要智力≥普通，你当前智力不足", 0
    if "智力≥优良" in attr_req and player.get("intelligence", "平庸") not in ("优良", "卓越"):
        return False, f"{strategy_name}需要智力≥优良", 0
    if "政治≥优良" in attr_req and player.get("politics", "拙劣") not in ("优良", "卓越"):
        return False, f"{strategy_name}需要政治≥优良", 0
    if "政治≥普通" in attr_req and player.get("politics", "拙劣") in ("拙劣", "平庸"):
        return False, f"{strategy_name}需要政治≥普通", 0
    if "军事≥普通" in attr_req and player.get("military", "平庸") not in ("普通", "优良", "卓越"):
        return False, f"{strategy_name}需要军事≥普通", 0
    if "权力值≥地方" in attr_req:
        power_order = ["微末", "小吏", "地方", "朝堂", "权倾"]
        try:
            pidx = power_order.index(player.get("power", "微末"))
            if pidx < power_order.index("地方"):
                return False, f"{strategy_name}需要权力值≥地方", 0
        except ValueError:
            return False, f"{strategy_name}需要权力值≥地方", 0

    # 成功率判定（基于属性+市场环境）
    base_success = 0.5
    if "优良" in player.get("intelligence", "平庸"):
        base_success += 0.15
    if "优良" in player.get("politics", "平庸"):
        base_success += 0.10

    # 市场环境修正
    conditions = get_market_conditions(player.get("current_time", ""))
    if conditions:
        base_success += 0.05

    success = random.random() < base_success

    # 结果
    if success:
        profit = random.randint(50, 200)
        return True, strat["成功标志"], profit
    else:
        loss = random.randint(20, 150)
        return False, strat["失败标志"], -loss


def get_available_strategies(player):
    """获取当前可用的高级策略列表"""
    available = []
    for name, strat in ADVANCED_STRATEGIES.items():
        attr_req = strat["属性要求"]
        skill_req = strat["技能要求"]

        # 简化的属性/技能检查
        blocked = False
        if "智力≥优良" in attr_req and player.get("intelligence", "") not in ("优良", "卓越"):
            blocked = True
        if "智力≥普通" in attr_req and player.get("intelligence", "") not in ("普通", "优良", "卓越"):
            blocked = True
        if "政治≥优良" in attr_req and player.get("politics", "") not in ("优良", "卓越"):
            blocked = True
        if "政治≥普通" in attr_req and player.get("politics", "") in ("拙劣", "平庸"):
            blocked = True
        if "军事≥普通" in attr_req and player.get("military", "") not in ("普通", "优良", "卓越"):
            blocked = True
        if "权力值≥地方" in attr_req:
            power_order = ["微末", "小吏", "地方", "朝堂", "权倾"]
            try:
                if power_order.index(player.get("power", "微末")) < power_order.index("地方"):
                    blocked = True
            except ValueError:
                blocked = True

        available.append({
            "名称": name,
            "属性要求": attr_req,
            "技能要求": skill_req,
            "可用": not blocked,
            "风险": strat["风险"],
        })

    return available
