"""
《宣和二年》Flask API服务器
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from engine.db import init_db, player_exists, get_player
from engine.game_engine import char_create, process_action, month_settle as do_month_settle, format_status_line, TRAIT_MODS, IDENTITY_BASE
from engine.ai_narrator import get_ai_status, load_config, save_config
from engine.db import get_npcs, get_npc, init_npc_data, get_npc_count_for_user
from engine.tech_tree import get_tech_tree, get_tech_status, can_research_tech, research_tech
from engine.exam import get_exam_question, grade_answer, get_player_exam_level

app = Flask(__name__, static_folder='../static', template_folder='../templates')

# 自动初始化数据库，失败时打印到日志
try:
    init_db()
    print("数据库初始化成功")
except Exception as e:
    print(f"数据库初始化失败: {e}")
    import traceback
    traceback.print_exc()


@app.route('/api/dbcheck')
def db_check():
    """数据库诊断"""
    result = {
        "DATABASE_URL_set": bool(os.environ.get("DATABASE_URL", "")),
        "python_version": sys.version,
    }
    try:
        from engine.db import get_db
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1")
        result["db_connect"] = "OK"
        conn.close()
    except Exception as e:
        result["db_connect"] = str(e)
    return jsonify(result)


# 简单的user_id映射（单用户模式）
DEFAULT_USER = "player_1"


@app.route('/')
def index():
    """返回游戏主页面"""
    return send_from_directory(app.template_folder, 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前游戏状态"""
    if not player_exists(DEFAULT_USER):
        return jsonify({"exists": False})
    player = get_player(DEFAULT_USER)
    return jsonify({"exists": True, "player": player})


@app.route('/api/create', methods=['POST'])
def create_character():
    """创建角色"""
    data = request.json
    required = ['name', 'gender', 'age', 'faction', 'identity', 'trait']
    for field in required:
        if field not in data or not data[field]:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400

    if player_exists(DEFAULT_USER):
        return jsonify({"error": "角色已存在，请先删除"}), 400

    result = char_create(
        user_id=DEFAULT_USER,
        name=data['name'],
        gender=data['gender'],
        age=data['age'],
        faction=data['faction'],
        identity=data['identity'],
        trait=data['trait'],
        location=data.get('location', ''),
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/action', methods=['POST'])
def handle_action():
    """处理玩家行动"""
    data = request.json
    user_input = data.get('input', '').strip()

    if not user_input:
        return jsonify({"error": "请输入行动指令"}), 400

    if not player_exists(DEFAULT_USER):
        return jsonify({"error": "请先创建角色"}), 400

    result = process_action(DEFAULT_USER, user_input)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/month_settle', methods=['POST'])
def month_settle():
    """手动触发过月"""
    if not player_exists(DEFAULT_USER):
        return jsonify({"error": "请先创建角色"}), 400

    result = do_month_settle(DEFAULT_USER)
    return jsonify(result)


@app.route('/api/reset', methods=['POST'])
def reset_game():
    """重置游戏（删除角色）"""
    from engine.db import get_db, DATABASE_URL
    conn = get_db()
    ph = '%s' if DATABASE_URL else '?'
    tables = ['player', 'npc', 'skills', 'items', 'followers', 'world']
    for t in tables:
        conn.execute(f"DELETE FROM {t} WHERE user_id={ph}", (DEFAULT_USER,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/api/traits/<faction>', methods=['GET'])
def get_traits(faction):
    """获取特质列表（随机5项）"""
    import random
    all_traits = list(TRAIT_MODS.keys())
    selected = random.sample(all_traits, min(5, len(all_traits)))
    trait_info = []
    for t in selected:
        mods = TRAIT_MODS.get(t, {})
        effect = "、".join([f"{k}{v}" for k, v in mods.items()]) if mods else "特殊效果（非数值类）"
        trait_info.append({"name": t, "effect": effect})
    return jsonify({"traits": trait_info})


@app.route('/api/identities/<faction>', methods=['GET'])
def get_identities(faction):
    """获取某势力的身份列表"""
    identities = IDENTITY_BASE.get(faction, IDENTITY_BASE["宋"])
    result = []
    for name, attrs in identities.items():
        result.append({
            "name": name,
            "attrs": attrs
        })
    return jsonify({"identities": result})


@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """获取AI配置状态"""
    return jsonify(get_ai_status())


@app.route('/api/ai/config', methods=['POST'])
def ai_config():
    """更新AI配置"""
    data = request.json
    cfg = load_config()

    # 切换提供商
    if 'provider' in data:
        provider = data['provider']
        if provider in ('deepseek', 'ollama', 'coze'):
            cfg['provider'] = provider

    # DeepSeek 配置
    if 'deepseek_api_key' in data:
        cfg.setdefault('deepseek', {})['api_key'] = data['deepseek_api_key']
    if 'deepseek_model' in data:
        cfg.setdefault('deepseek', {})['model'] = data['deepseek_model']

    # Ollama 配置
    if 'ollama_base_url' in data:
        cfg.setdefault('ollama', {})['base_url'] = data['ollama_base_url']
    if 'ollama_model' in data:
        cfg.setdefault('ollama', {})['model'] = data['ollama_model']

    # Coze 配置
    if 'coze_api_key' in data:
        cfg.setdefault('coze', {})['api_key'] = data['coze_api_key']
    if 'coze_bot_id' in data:
        cfg.setdefault('coze', {})['bot_id'] = data['coze_bot_id']

    save_config(cfg)
    return jsonify({"success": True, "status": get_ai_status()})


@app.route('/api/ai/test', methods=['POST'])
def ai_test():
    """测试AI连接"""
    from engine.ai_narrator import generate_narrative_ai
    try:
        text, ai_used, error = generate_narrative_ai(
            action_type="日常",
            success=True,
            detail="在汴京街巷闲逛",
            npc="",
            action="闲逛街头",
            player={"faction": "宋", "identity": "平民", "name": "测试", "location": "汴京", "money": 10, "energy": 25},
        )
        return jsonify({
            "success": ai_used,
            "narrative": text,
            "error": error,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "narrative": None,
            "error": str(e),
        })


# ==================== NPC API ====================

@app.route('/api/npcs', methods=['GET'])
def npc_list():
    """获取所有NPC列表"""
    faction = request.args.get('faction', '')
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"error": "请先创建角色"}), 400

    if faction:
        from engine.db import get_db, DATABASE_URL
        conn = get_db()
        ph = '%s' if DATABASE_URL else '?'
        rows = conn.execute(
            f"SELECT * FROM npc WHERE user_id={ph} AND npc_faction={ph} AND is_active='true' ORDER BY bond",
            (user_id, faction)
        ).fetchall()
        conn.close()
    else:
        rows = get_npcs(user_id)

    npcs = [dict(r) for r in rows]
    return jsonify({"npcs": npcs, "count": len(npcs)})


@app.route('/api/npcs/count', methods=['GET'])
def npc_count():
    """NPC数量统计"""
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"count": 0})
    cnt = get_npc_count_for_user(user_id)
    return jsonify({"count": cnt})


# ==================== 科技 API ====================

@app.route('/api/tech/tree', methods=['GET'])
def tech_tree():
    """获取完整科技树"""
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"error": "请先创建角色"}), 400
    status = get_tech_status(user_id)
    return jsonify(status)


@app.route('/api/tech/research', methods=['POST'])
def tech_research():
    """研发科技"""
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"error": "请先创建角色"}), 400

    data = request.json
    tech_name = data.get('tech_name', '')
    if not tech_name:
        return jsonify({"error": "请指定科技名称"}), 400

    if not can_research_tech(user_id, tech_name):
        return jsonify({"error": "无法研发该科技（前置未完成或已完成）"}), 400

    result = research_tech(user_id, tech_name, research_points=data.get('points', 20))
    return jsonify(result)


# ==================== 科举 API ====================

@app.route('/api/exam/question', methods=['GET'])
def exam_question():
    """获取科举题目"""
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"error": "请先创建角色"}), 400

    player = get_player(user_id)
    level_name, total_score = get_player_exam_level(player)
    topic_type = request.args.get('type', '')
    question = get_exam_question(level_name, topic_type if topic_type else None)

    return jsonify({
        "question": question,
        "level": level_name,
        "total_score": total_score,
    })


@app.route('/api/exam/answer', methods=['POST'])
def exam_answer():
    """提交科举作答"""
    user_id = DEFAULT_USER
    if not player_exists(user_id):
        return jsonify({"error": "请先创建角色"}), 400

    data = request.json
    answer = data.get('answer', '').strip()
    if not answer or len(answer) < 5:
        return jsonify({"error": "请完整作答"}), 400

    player = get_player(user_id)
    question = data.get('question', {})

    result = grade_answer(player, question, answer)

    # 更新积分
    score = result['score']
    old_total = player.get('exam_total_score', 0)
    player['exam_total_score'] = old_total + score

    from engine.db import save_player as db_save
    db_save(user_id, {'exam_total_score': player['exam_total_score']})

    return jsonify({
        "result": result,
        "old_total": old_total,
        "new_total": player['exam_total_score'],
        "level": get_player_exam_level(player),
    })


if __name__ == '__main__':
    print("=" * 50)
    print("《宣和二年》游戏服务器启动")
    print("访问 http://localhost:5000 开始游戏")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
