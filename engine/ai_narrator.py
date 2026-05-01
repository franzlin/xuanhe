"""
《宣和二年》AI叙事生成器
支持 DeepSeek / Ollama / Coze 三种后端，通过配置切换
"""

import json
import os
import random
import requests

# ============================================================
# 配置
# ============================================================

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'ai_config.json')

DEFAULT_CONFIG = {
    "provider": "deepseek",
    "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "max_tokens": 300,
        "temperature": 0.85,
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "qwen2.5:7b",
    },
    "coze": {
        "bot_id": "",
        "api_key": "",
        "base_url": "https://api.coze.cn",
    }
}


def load_config():
    """加载AI配置"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            # 合并默认值，确保新字段存在
            for key in DEFAULT_CONFIG:
                if key not in cfg:
                    cfg[key] = DEFAULT_CONFIG[key]
                elif isinstance(DEFAULT_CONFIG[key], dict):
                    for k2 in DEFAULT_CONFIG[key]:
                        if k2 not in cfg[key]:
                            cfg[key][k2] = DEFAULT_CONFIG[key][k2]
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    """保存AI配置"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ============================================================
# 系统提示词
# ============================================================

SYSTEM_PROMPT = """你是《宣和二年》的文字推演游戏叙事AI。

【时代背景】
北宋宣和二年（1120年）。方腊起义于江南，金国崛起于白山黑水，辽朝日薄西山，西夏据西北虎视，蒙古部落暗流涌动。朝中蔡京、童贯权倾朝野，士大夫清议不绝。天下大势，棋局已开。

【你的职责】
将玩家的行动转化为沉浸式叙事文本。你不是GM，你是执笔人——用文字让这个时代活过来。

【写作规则】
1. 古风半文言，简洁有力。不要翻译腔，不要网文腔，要有史传笔意
2. 第三人称，如"李某""此人"，偶以"你"代之亦可
3. 每段50-150字，不可过长
4. 根据行动类型切换腔调：官场→含蓄锋利，江湖→豪快磊落，市井→俚俗生动，战场→肃杀苍凉
5. 成功不可过于顺遂，失败亦须留有余地——史书不留爽文
6. 每次生成须有变化，不得重复套话
7. 只输出叙事文本，不加任何解释、标注或前缀
8. 人名、地名、官名须符合宋代规制"""


# ============================================================
# 用户提示构建
# ============================================================

ACTION_ATMOSPHERE = {
    "日常": "市井烟火，柴米油盐",
    "功名": "科举文场，寒窗苦读",
    "经营": "商贾之道，锱铢必较",
    "战斗": "兵戈相向，生死须臾",
    "犯罪": "暗夜行路，刀尖舔血",
    "风月": "红袖添香，风月无边",
    "社交": "人情往来，杯酒言欢",
}

BATTLE_RESULT_ATMOSPHERE = {
    "大胜": "势如破竹，敌军溃散",
    "胜": "略占上风，尚有余力",
    "僵持": "双方角力，胜负未分",
    "败": "力有未逮，暂且退却",
    "惨败": "兵败如山，元气大伤",
}


def build_user_prompt(action_type, success, detail="", npc="", action="",
                      casualties=0, loot=0, player=None, extra_context=None):
    """构建发送给AI的用户提示"""

    # 基础信息
    lines = []
    lines.append(f"【行动类型】{action_type}")
    lines.append(f"【结果】{'成功' if success else '失败'}")
    lines.append(f"【玩家行动】{action}")

    if npc:
        lines.append(f"【相关人物】{npc}")
    if detail:
        lines.append(f"【详情】{detail}")
    if casualties > 0:
        lines.append(f"【伤亡】{casualties}人")
    if loot > 0:
        lines.append(f"【缴获】{loot}贯")

    # 玩家状态摘要
    if player:
        state_parts = []
        if player.get('faction'):
            state_parts.append(f"{player['faction']}·{player.get('identity', '')}")
        if player.get('name'):
            state_parts.append(f"名{player['name']}")
        if player.get('location'):
            state_parts.append(f"身在{player['location']}")
        if player.get('money') is not None:
            state_parts.append(f"资{player['money']}贯")
        if player.get('energy') is not None:
            state_parts.append(f"精力{player['energy']}")
        if state_parts:
            lines.append(f"【身份】{'，'.join(state_parts)}")

    # 氛围提示
    if action_type == "战斗":
        for br in BATTLE_RESULT_ATMOSPHERE:
            if br in detail:
                lines.append(f"【氛围】{BATTLE_RESULT_ATMOSPHERE[br]}")
                break
        else:
            lines.append(f"【氛围】{ACTION_ATMOSPHERE.get(action_type, '世事无常')}")
    else:
        lines.append(f"【氛围】{ACTION_ATMOSPHERE.get(action_type, '世事无常')}")

    if extra_context:
        lines.append(f"【额外信息】{extra_context}")

    lines.append("\n请生成叙事文本。")

    return "\n".join(lines)


# ============================================================
# AI后端调用
# ============================================================

def _call_deepseek(user_prompt, config):
    """调用DeepSeek API（兼容OpenAI格式）"""
    ds = config.get('deepseek', {})
    api_key = ds.get('api_key', '')
    if not api_key:
        raise ValueError("DeepSeek API Key 未配置")

    base_url = ds.get('base_url', 'https://api.deepseek.com/v1').rstrip('/')
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": ds.get('model', 'deepseek-chat'),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": ds.get('max_tokens', 300),
        "temperature": ds.get('temperature', 0.85),
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    content = data['choices'][0]['message']['content'].strip()
    # 清理可能的引号包裹
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    return content


def _call_ollama(user_prompt, config):
    """调用Ollama本地模型"""
    ol = config.get('ollama', {})
    base_url = ol.get('base_url', 'http://localhost:11434').rstrip('/')
    url = f"{base_url}/api/chat"

    payload = {
        "model": ol.get('model', 'qwen2.5:7b'),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.85,
            "num_predict": 300,
        }
    }

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    content = data.get('message', {}).get('content', '').strip()
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    return content


def _call_coze(user_prompt, config):
    """调用Coze Bot API"""
    cz = config.get('coze', {})
    api_key = cz.get('api_key', '')
    bot_id = cz.get('bot_id', '')
    if not api_key or not bot_id:
        raise ValueError("Coze API Key 或 Bot ID 未配置")

    base_url = cz.get('base_url', 'https://api.coze.cn').rstrip('/')
    url = f"{base_url}/v3/chat"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Coze v3 API 使用流式+轮询模式
    import uuid
    user_id = str(uuid.uuid4())

    payload = {
        "bot_id": bot_id,
        "user_id": user_id,
        "stream": False,
        "auto_save_history": True,
        "additional_messages": [
            {
                "role": "user",
                "content": user_prompt,
                "content_type": "text",
            }
        ]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Coze v3 返回 chat id，需要轮询获取结果
    chat_id = data.get('data', {}).get('id')
    conversation_id = data.get('data', {}).get('conversation_id')

    if not chat_id:
        raise ValueError(f"Coze 返回异常: {data}")

    # 轮询获取结果（最多等20秒）
    import time
    check_url = f"{base_url}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
    for _ in range(10):
        time.sleep(2)
        check_resp = requests.get(check_url, headers=headers, timeout=10)
        check_data = check_resp.json()
        status = check_data.get('data', {}).get('status', '')
        if status == 'completed':
            break
        if status in ('failed', 'requires_action'):
            raise ValueError(f"Coze 对话失败: status={status}")

    # 获取消息列表
    msg_url = f"{base_url}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
    msg_resp = requests.get(msg_url, headers=headers, timeout=10)
    msg_data = msg_resp.json()

    messages = msg_data.get('data', [])
    for msg in messages:
        if msg.get('role') == 'assistant' and msg.get('type') == 'answer':
            content = msg.get('content', '').strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content

    raise ValueError("Coze 未返回有效回复")


# ============================================================
# 主入口：AI叙事生成
# ============================================================

def generate_narrative_ai(action_type, success, detail="", npc="", action="",
                          casualties=0, loot=0, player=None, extra_context=None):
    """
    AI叙事生成主函数
    返回 (narrative_text, ai_used, error_msg)
    - ai_used: bool，是否使用了AI
    - error_msg: str，如果AI失败则返回错误信息，否则为None
    """
    config = load_config()
    provider = config.get('provider', 'deepseek')

    user_prompt = build_user_prompt(
        action_type, success, detail, npc, action,
        casualties, loot, player, extra_context
    )

    try:
        if provider == 'deepseek':
            text = _call_deepseek(user_prompt, config)
        elif provider == 'ollama':
            text = _call_ollama(user_prompt, config)
        elif provider == 'coze':
            text = _call_coze(user_prompt, config)
        else:
            raise ValueError(f"未知的AI提供商: {provider}")

        # 安全检查：AI返回空或太短
        if not text or len(text) < 5:
            raise ValueError("AI返回内容过短")

        return text, True, None

    except Exception as e:
        return None, False, str(e)


def get_ai_status():
    """获取AI配置状态（隐藏API Key中间位）"""
    config = load_config()
    provider = config.get('provider', 'deepseek')

    status = {
        "provider": provider,
        "configured": False,
        "providers": {}
    }

    for p in ['deepseek', 'ollama', 'coze']:
        p_cfg = config.get(p, {})
        if p == 'deepseek':
            key = p_cfg.get('api_key', '')
            has_key = bool(key)
            masked = key[:4] + '****' + key[-4:] if len(key) > 8 else ('已设置' if key else '未设置')
            status['providers'][p] = {
                "configured": has_key,
                "api_key_display": masked,
                "model": p_cfg.get('model', ''),
            }
            if p == provider:
                status['configured'] = has_key
        elif p == 'ollama':
            status['providers'][p] = {
                "configured": True,  # Ollama不需要key
                "base_url": p_cfg.get('base_url', ''),
                "model": p_cfg.get('model', ''),
            }
        elif p == 'coze':
            key = p_cfg.get('api_key', '')
            has_key = bool(key) and bool(p_cfg.get('bot_id', ''))
            status['providers'][p] = {
                "configured": has_key,
                "model": p_cfg.get('bot_id', ''),
            }
            if p == provider:
                status['configured'] = has_key

    return status
