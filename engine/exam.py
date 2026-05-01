"""
《宣和二年》科举答题系统
严格遵循北宋宣和年间的科举制度：
发解试（州试）→ 省试（礼部试）→ 殿试（御试）
P0规则：禁止"童试""秀才""举人功名"等明清概念
"""
import json
import random
from .ai_narrator import load_config

# ============================================================
# 科举等级定义（对齐《核心机制》§13）
# ============================================================

EXAM_LEVELS = [
    {"name": "发解试", "min_score": 0, "prestige_bonus": 5, "energy_cost": 5,
     "timing": "秋季", "location": "本州贡院", "topics": ["帖经","墨义","诗赋","策论"],
     "admit_rate": "10-15%", "title": "举人（获解送赴京资格）", "desc": "州府选拔试，户籍所在州报名"},
    {"name": "省试", "min_score": 30, "prestige_bonus": 20, "energy_cost": 7,
     "timing": "次年春", "location": "汴京礼部贡院", "topics": ["经义","诗赋","策论"],
     "admit_rate": "≤5%", "title": "贡士（获殿试资格）", "desc": "礼部主持，糊名+誊录+锁院"},
    {"name": "殿试", "min_score": 60, "prestige_bonus": 40, "energy_cost": 10,
     "timing": "省试后", "location": "崇政殿", "topics": ["策问"],
     "admit_rate": "不黜落仅定名次", "title": "进士及第/出身", "desc": "天子亲临，策问一道"},
]

# ============================================================
# 朝廷对策题库（对齐《核心机制》科举策问/答辩） 
# ============================================================

CEWEN_BANK = [
    {
        "title": "论西北边防策",
        "topic": "策问",
        "background": "宣和年间，金崛起辽东，辽日薄西山。大宋北境面临变局。朝中有人主张联金灭辽收复燕云；有人力陈唇亡齿寒。",
        "question": "若你为当朝重臣，论大宋应以何种策略应对北方变局？",
        "key_points": ["边防形势", "战略取舍", "具体措施"],
        "difficulty": 3,
    },
    {
        "title": "花石纲利弊议",
        "topic": "策问",
        "background": "朝廷修艮岳，命朱勔主持花石纲。东南百姓苦不堪言，方腊趁机聚众起事。",
        "question": "论花石纲于国于民利弊几何？若为地方官，当如何应对？",
        "key_points": ["民生影响", "政治风险", "治理对策"],
        "difficulty": 2,
    },
    {
        "title": "论东南民变根源",
        "topic": "策问",
        "background": "宣和二年，方腊在睦州以摩尼教聚众起事，旬月间拥兵数十万，震动江南。",
        "question": "论方腊之乱根本原因何在？朝廷应如何根除民变之患？",
        "key_points": ["根源分析", "各因素比重", "长治久安之策"],
        "difficulty": 3,
    },
    {
        "title": "熙宁变法得失论",
        "topic": "策问",
        "background": "神宗时王安石推行新法，青苗、免役、保甲、市易诸法争议至今。元祐更化后新法多废。",
        "question": "王安石变法为何功败垂成？若你主政，当如何取其利而避其害？",
        "key_points": ["利弊分析", "失败原因", "调和之道"],
        "difficulty": 4,
    },
    {
        "title": "论漕运与国计",
        "topic": "策问",
        "background": "汴京百万军民，粮米仰赖东南漕运。黄河水患频发，漕河淤塞日重。",
        "question": "漕运乃京师命脉，如何确保其畅通？河道与海运利弊各如何？",
        "key_points": ["漕运现状", "方案比较", "具体建议"],
        "difficulty": 2,
    },
    {
        "title": "论选官制度兴革",
        "topic": "策问",
        "background": "大宋以科举取士，文武分途。近年恩荫过滥，冗官之弊日显。",
        "question": "当前选官制度有何弊端？应如何改革？",
        "key_points": ["现状诊断", "改革方向", "阻力预估"],
        "difficulty": 3,
    },
    {
        "title": "论茶盐专卖利弊",
        "topic": "策问",
        "background": "茶盐为朝廷专卖之物，岁入甚丰。然走私猖獗，官民矛盾加剧。",
        "question": "茶盐专卖制度是否应当继续？若改，当如何改？",
        "key_points": ["经济账", "民生账", "改革方案"],
        "difficulty": 2,
    },
    {
        "title": "黄河治水策",
        "topic": "策问",
        "background": "黄河屡决，淹没千里。历代治河之法，宽堤疏浚、束水攻沙、分流减势，莫衷一是。",
        "question": "黄河之患根本在何处？你主张何种治河之策？",
        "key_points": ["灾害根源", "方案比较", "实施可行性"],
        "difficulty": 3,
    },
    {
        "title": "论用兵与养兵之道",
        "topic": "策问",
        "background": "大宋养兵百万，岁费占国用大半。禁军骄惰，厢军冗杂。西军虽精，远水难救近火。",
        "question": "大宋兵制之弊在何处？不额外增赋，如何强军？",
        "key_points": ["兵制诊断", "财政约束", "改革路径"],
        "difficulty": 4,
    },
    {
        "title": "论工商与农本",
        "topic": "策问",
        "background": "大宋工商繁盛，市舶之利甚厚。朝中重农抑商之声未绝。",
        "question": "工商繁荣是否威胁农本？朝廷应以何种态度对待商人？",
        "key_points": ["农工商关系", "各业贡献", "政策建议"],
        "difficulty": 2,
    },
]

# 经义题库
JINGYI_BANK = [
    {"title":"论《大学》「明明德」","topic":"经义","background":"《大学》开篇：大学之道，在明明德，在亲民，在止于至善。",
     "question":"解释「明明德」之义，论其为学之序与为政之道如何贯通。","key_points":["义理解释","修身","为政"],"difficulty":2},
    {"title":"论《中庸》之「诚」","topic":"经义","background":"《中庸》：诚者，天之道也；诚之者，人之道也。",
     "question":"论「诚」在儒家思想中的根本地位，以及如何由诚达至中和。","key_points":["诚之定义","天道人道","修养路径"],"difficulty":3},
    {"title":"论「君子和而不同」","topic":"经义","background":"子曰：君子和而不同，小人同而不和。",
     "question":"解释此语之义，举史实说明在朝堂议事中的运用。","key_points":["释义","和同之辨","朝政应用"],"difficulty":2},
    {"title":"论《孟子》「民为贵」","topic":"经义","background":"孟子曰：民为贵，社稷次之，君为轻。",
     "question":"论孟子此言之本义，及其对当代治国的现实意义。","key_points":["本义阐释","君民关系","当代运用"],"difficulty":3},
    {"title":"论《春秋》大义","topic":"经义","background":"《春秋》一字褒贬，所谓微言大义。",
     "question":"《春秋》之「大义」为何？后人当以何种态度研读？","key_points":["微言大义","读法","当代之用"],"difficulty":4},
    {"title":"论「穷则变」","topic":"经义","background":"《易·系辞》：穷则变，变则通，通则久。",
     "question":"以古今治乱兴衰之事，阐释穷则变之理。","key_points":["经典释义","历史例证","时政借鉴"],"difficulty":2},
    {"title":"论「义利之辨」","topic":"经义","background":"孟子见梁惠王，王曰亦有以利吾国乎，孟子对曰何必曰利。",
     "question":"论义利之辨的核心要义，在朝廷政务中如何处理义与利之关系。","key_points":["义利之辨","历史争议","现实平衡"],"difficulty":3},
    {"title":"论「民惟邦本」","topic":"经义","background":"《尚书》：民惟邦本，本固邦宁。",
     "question":"阐发此语深意，结合当代民生疾苦论为政之要。","key_points":["经义阐发","民生关联","政策启示"],"difficulty":2},
]

# 诗赋主题（发解试/省试用）
SHIFU_TOPICS = [
    {"title":"《秋日登高》","topic":"诗赋","instruction":"以'秋日登高远眺'为题，作五言律诗一首。意境须有壮阔感。","difficulty":1},
    {"title":"《咏雪》","topic":"诗赋","instruction":"以'雪'为题，作七言绝句一首。须清冷隽永。","difficulty":1},
    {"title":"《边塞》","topic":"诗赋","instruction":"以'边塞'为题，作五言律诗一首。须苍凉悲壮。","difficulty":2},
    {"title":"《春雨》","topic":"诗赋","instruction":"以'春雨'为题，作七言律诗一首。须润物细无声之意境。","difficulty":2},
    {"title":"《送友人》","topic":"诗赋","instruction":"以'送别友人'为题，作七言绝句一首。情深义重而不矫揉。","difficulty":1},
]


def get_exam_question(level_name, topic_type=None):
    """获取科举题目，根据等级匹配题型"""
    if level_name == "殿试" or topic_type == "策问":
        bank = CEWEN_BANK
    elif level_name == "省试":
        if topic_type in ("经义","诗赋"):
            bank = JINGYI_BANK if topic_type == "经义" else [t for t in SHIFU_TOPICS]  # convert to list
        else:
            bank = CEWEN_BANK + JINGYI_BANK
        return random.choice(bank)
    elif level_name == "发解试":
        # 发解试：帖经/墨义/诗赋/策论 四类
        if topic_type == "诗赋":
            return random.choice(SHIFU_TOPICS)
        else:
            return random.choice(CEWEN_BANK[:5] + JINGYI_BANK[:4])
    else:
        return random.choice(CEWEN_BANK[:5])


def grade_answer(player, question, answer):
    """
    AI评分（对齐科举策问/答辩机制）
    返回 {score, literary, logic, insight, comment, passed}
    """
    detail = f"题目：{question.get('title','')}。考生作答：{answer}"

    from .ai_narrator import generate_narrative_ai
    text, ai_used, error = generate_narrative_ai(
        action_type="功名",
        success=True,
        detail=detail,
        action=f"参加{question.get('topic','科举')}：{question.get('title','')}",
        player=player,
        extra_context=f"""这是宋代科举评分，不是叙事生成。请按格式评分（只返回JSON）：
{{
  "score": <0-100的总分>,
  "literary": <0-30的文采分>,
  "logic": <0-30的逻辑分>,
  "insight": <0-40的见识分>,
  "comment": "<20-50字简评，需有宋人风范>"
}}
题目类型：{question.get('topic')}
难度：{'★★★★' if question.get('difficulty',2)>3 else '★★' if question.get('difficulty',2)<=2 else '★★★'}"""
    )

    if ai_used and text:
        try:
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(text[json_start:json_end])
                if 'score' in result:
                    result['passed'] = result['score'] >= 40
                    return result
        except (json.JSONDecodeError, ValueError):
            pass

    return _rule_based_grade(player, question, answer)


def _rule_based_grade(player, question, answer):
    """AI不可用时的规则评分降级"""
    score = 50
    if len(answer) > 100: score += 10
    if len(answer) > 200: score += 10
    if len(answer) > 400: score += 10

    key_words = ["当","者","也","之","以","而","故","非","然则","是故","何也"]
    for kw in key_words:
        if kw in answer: score += 1
    score = min(score, 95)

    intel = player.get('intelligence', '普通')
    intel_bonus = {"拙劣": -10, "平庸": -5, "普通": 0, "优良": 5, "卓越": 10}
    score += intel_bonus.get(intel, 0)
    score = max(0, min(100, score))

    return {
        "score": score,
        "literary": min(30, score//3),
        "logic": min(30, score//3),
        "insight": min(40, score//2),
        "comment": "文理尚可" if score>=60 else "还需用功" if score>=40 else "文理未通",
        "passed": score >= 40,
    }


def get_player_exam_level(player):
    """获取玩家当前科举水平"""
    total_score = player.get('exam_total_score', 0)
    current = "发解试"
    for level in reversed(EXAM_LEVELS):
        if total_score >= level['min_score']:
            current = level['name']
            break
    return current, total_score


def get_exam_info(level_name):
    """获取科举等级详细信息"""
    for level in EXAM_LEVELS:
        if level['name'] == level_name:
            return level
    return EXAM_LEVELS[0]
