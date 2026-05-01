"""
《宣和二年》数据库管理模块
支持：本地SQLite / 云端PostgreSQL 自动切换
"""
import json
import os
import time

# 数据库连接：优先使用环境变量（Railway/云平台自动注入）
DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_db():
    """获取数据库连接 - 自动适配SQLite或PostgreSQL"""
    if DATABASE_URL:
        return _get_pg()
    return _get_sqlite()

def _get_sqlite():
    """SQLite本地连接"""
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'xuanhe.db')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _get_pg():
    """PostgreSQL云端连接"""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    # 使cursor返回dict-like行
    def _dict_row(cursor):
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        return lambda *args: dict(zip(cols, args))
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def init_db():
    """初始化数据库，创建所有表"""
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)

    # PostgreSQL用TEXT替代部分类型
    int_def = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    auto_id = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_def = "TEXT"  # 通用

    c.execute(f'''CREATE TABLE IF NOT EXISTS player (
        user_id {text_def} PRIMARY KEY,
        name {text_def} DEFAULT '',
        gender {text_def} DEFAULT '男',
        age INTEGER DEFAULT 18,
        identity {text_def} DEFAULT '平民',
        faction {text_def} DEFAULT '宋',
        traits {text_def} DEFAULT '[]',
        intelligence {text_def} DEFAULT '平庸',
        military {text_def} DEFAULT '平庸',
        politics {text_def} DEFAULT '拙劣',
        alertness {text_def} DEFAULT '低',
        charm {text_def} DEFAULT '平庸',
        malice {text_def} DEFAULT '中',
        greed {text_def} DEFAULT '中',
        loyalty_court {text_def} DEFAULT '中',
        loyalty_faction {text_def} DEFAULT '中',
        money REAL DEFAULT 0,
        health {text_def} DEFAULT '康健',
        health_trend {text_def} DEFAULT '稳固',
        health_status {text_def} DEFAULT '[]',
        energy INTEGER DEFAULT 30,
        energy_cap INTEGER DEFAULT 30,
        official_rank {text_def} DEFAULT '白身',
        troops INTEGER DEFAULT 0,
        prestige {text_def} DEFAULT '默默无闻',
        prestige_official {text_def} DEFAULT '默默无闻',
        prestige_civilian {text_def} DEFAULT '默默无闻',
        prestige_literary {text_def} DEFAULT '默默无闻',
        prestige_martial {text_def} DEFAULT '默默无闻',
        prestige_wealth {text_def} DEFAULT '默默无闻',
        prestige_jianghu {text_def} DEFAULT '默默无闻',
        power {text_def} DEFAULT '微末',
        exposure_risk {text_def} DEFAULT '安全',
        personality_yili {text_def} DEFAULT '中正',
        personality_gangrou {text_def} DEFAULT '中正',
        personality_kuanxia {text_def} DEFAULT '中正',
        personality_danyong {text_def} DEFAULT '中正',
        yili_actions INTEGER DEFAULT 0,
        gangrou_actions INTEGER DEFAULT 0,
        kuanxia_actions INTEGER DEFAULT 0,
        danyong_actions INTEGER DEFAULT 0,
        personal_desire {text_def} DEFAULT '',
        desire_stage {text_def} DEFAULT '未启程',
        location {text_def} DEFAULT '东京开封府',
        current_time {text_def} DEFAULT '宣和二年正月',
        month_days_elapsed INTEGER DEFAULT 0,
        total_months_played INTEGER DEFAULT 0,
        crime_this_month INTEGER DEFAULT 0,
        event_count_this_month INTEGER DEFAULT 0,
        acquisitions {text_def} DEFAULT '[]',
        created_at {text_def} DEFAULT '',
        grudges {text_def} DEFAULT '{{}}',
        titles {text_def} DEFAULT '[]',
        milestones {text_def} DEFAULT '[]',
        faction_alignment {text_def} DEFAULT '',
        exam_total_score INTEGER DEFAULT 0
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS npc (
        id {auto_id},
        user_id {text_def} DEFAULT '',
        name {text_def} DEFAULT '',
        bond {text_def} DEFAULT '寻常',
        tags {text_def} DEFAULT '[]',
        note {text_def} DEFAULT '',
        grudge_reason {text_def} DEFAULT '',
        grudge_level {text_def} DEFAULT '',
        npc_identity {text_def} DEFAULT '',
        npc_official_title {text_def} DEFAULT '',
        npc_party {text_def} DEFAULT '',
        npc_power {text_def} DEFAULT '微末',
        npc_faction {text_def} DEFAULT '',
        npc_age INTEGER DEFAULT 30,
        npc_health {text_def} DEFAULT '康健',
        npc_personality {text_def} DEFAULT '{{}}',
        npc_greed {text_def} DEFAULT '中',
        npc_malice {text_def} DEFAULT '中',
        npc_loyalty {text_def} DEFAULT '中',
        npc_intelligence {text_def} DEFAULT '普通',
        npc_military {text_def} DEFAULT '平庸',
        npc_alertness {text_def} DEFAULT '中',
        is_active {text_def} DEFAULT 'true',
        months_no_interact INTEGER DEFAULT 0
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS skills (
        id {auto_id},
        user_id {text_def} NOT NULL,
        skill_name {text_def} NOT NULL,
        level {text_def} DEFAULT '未涉猎',
        months_at_level INTEGER DEFAULT 0,
        high_value_actions INTEGER DEFAULT 0
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS items (
        id {auto_id},
        user_id {text_def},
        category {text_def} DEFAULT '',
        name {text_def} DEFAULT '',
        tags {text_def} DEFAULT '[]',
        status {text_def} DEFAULT '正常',
        detail {text_def} DEFAULT '',
        expire_month {text_def} DEFAULT '',
        acquired_month {text_def} DEFAULT ''
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS followers (
        id {auto_id},
        user_id {text_def},
        name {text_def} DEFAULT '',
        f_type {text_def} DEFAULT '',
        loyalty {text_def} DEFAULT '中',
        skill {text_def} DEFAULT '',
        salary REAL DEFAULT 0
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS world (
        id {auto_id},
        user_id {text_def} DEFAULT '',
        faction_name {text_def} DEFAULT '',
        influence {text_def} DEFAULT '中',
        treasury INTEGER DEFAULT 0,
        event_log {text_def} DEFAULT '',
        is_active {text_def} DEFAULT 'true'
    )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS tech_research (
        id {auto_id},
        user_id {text_def} NOT NULL,
        tech_name {text_def} NOT NULL,
        category {text_def} DEFAULT '',
        status {text_def} DEFAULT 'locked',
        research_points INTEGER DEFAULT 0,
        total_points_required INTEGER DEFAULT 100,
        started_month {text_def} DEFAULT '',
        completed_month {text_def} DEFAULT ''
    )''')

    conn.commit()
    if not is_pg:
        _migrate_schema_sqlite(conn)
    conn.close()


def _migrate_schema_sqlite(conn):
    """SQLite专用：给旧表添加可能缺少的新字段"""
    import sqlite3
    migrations = {
        "player": [
            "grudges TEXT DEFAULT '{}'",
            "titles TEXT DEFAULT '[]'",
            "milestones TEXT DEFAULT '[]'",
            "faction_alignment TEXT DEFAULT ''",
            "exam_total_score INTEGER DEFAULT 0",
        ],
        "npc": [
            "npc_official_title TEXT DEFAULT ''",
            "npc_party TEXT DEFAULT ''",
        ],
    }
    for table, new_cols in migrations.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col_def in new_cols:
            col_name = col_def.split()[0]
            if col_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    conn.commit()


# ==================== 通用CRUD ====================

def get_player(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM player WHERE user_id=?", (user_id,))
        row = c.fetchone()
    except Exception:
        c.execute("SELECT * FROM player WHERE user_id=%s", (user_id,))
        row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def save_player(user_id, data):
    """保存玩家数据（upsert：存在则更新，不存在则忽略）"""
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)

    fields = []
    values = []
    for k, v in data.items():
        if k == 'user_id':
            continue
        fields.append(f"{k}=?")
        values.append(v)
    values.append(user_id)

    if is_pg:
        set_clause = ', '.join(fields).replace('?', '%s')
        c.execute(f"UPDATE player SET {set_clause} WHERE user_id=%s", values)
    else:
        set_clause = ', '.join(fields)
        c.execute(f"UPDATE player SET {set_clause} WHERE user_id=?", values)
    conn.commit()
    conn.close()


def player_exists(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT 1 FROM player WHERE user_id=?", (user_id,))
        row = c.fetchone()
    except Exception:
        c.execute("SELECT 1 FROM player WHERE user_id=%s", (user_id,))
        row = c.fetchone()
    conn.close()
    return row is not None


def create_player(user_id, data):
    """创建新玩家"""
    conn = get_db()
    c = conn.cursor()
    data['user_id'] = user_id
    is_pg = bool(DATABASE_URL)

    cols = ', '.join(data.keys())
    placeholders = ', '.join(['%s' if is_pg else '?'] * len(data))
    try:
        c.execute(f"INSERT INTO player ({cols}) VALUES ({placeholders})", list(data.values()))
    except Exception:
        # 忽略重复插入
        pass
    conn.commit()
    conn.close()


# ==================== NPC CRUD（from SQLite only） ====================

def get_npcs(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM npc WHERE user_id=? AND is_active='true' ORDER BY bond", (user_id,))
    except Exception:
        c.execute("SELECT * FROM npc WHERE user_id=%s AND is_active='true' ORDER BY bond", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_npc(user_id, npc_name):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM npc WHERE user_id=? AND name=? AND is_active='true'", (user_id, npc_name))
    except Exception:
        c.execute("SELECT * FROM npc WHERE user_id=%s AND name=%s AND is_active='true'", (user_id, npc_name))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_npc(user_id, data):
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    data['user_id'] = user_id
    cols = ', '.join(data.keys())
    placeholders = ', '.join(['%s' if is_pg else '?'] * len(data))
    c.execute(f"INSERT INTO npc ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


def update_npc(user_id, npc_name, data):
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k}=?")
        values.append(v)
    values.extend([user_id, npc_name])
    if is_pg:
        set_clause = ', '.join(fields).replace('?', '%s')
        c.execute(f"UPDATE npc SET {set_clause} WHERE user_id=%s AND name=%s", values)
    else:
        set_clause = ', '.join(fields)
        c.execute(f"UPDATE npc SET {set_clause} WHERE user_id=? AND name=?", values)
    conn.commit()
    conn.close()


# ==================== Skills CRUD ====================

def get_skills(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM skills WHERE user_id=?", (user_id,))
    except Exception:
        c.execute("SELECT * FROM skills WHERE user_id=%s", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_skill(user_id, skill_name, level):
    conn = get_db()
    c = conn.cursor()
    try:
        if bool(DATABASE_URL):
            c.execute("INSERT INTO skills (user_id, skill_name, level) VALUES (%s,%s,%s)",
                      (user_id, skill_name, level))
        else:
            c.execute("INSERT INTO skills (user_id, skill_name, level) VALUES (?,?,?)",
                      (user_id, skill_name, level))
    except Exception:
        pass
    conn.commit()
    conn.close()


def update_skill(user_id, skill_name, data):
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k}=?")
        values.append(v)
    values.extend([user_id, skill_name])
    if is_pg:
        set_clause = ', '.join(fields).replace('?', '%s')
        c.execute(f"UPDATE skills SET {set_clause} WHERE user_id=%s AND skill_name=%s", values)
    else:
        c.execute(f"UPDATE skills SET {set_clause} WHERE user_id=? AND skill_name=?", values)
    conn.commit()
    conn.close()


# ==================== Items CRUD ====================

def get_items(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM items WHERE user_id=? ORDER BY acquired_month", (user_id,))
    except Exception:
        c.execute("SELECT * FROM items WHERE user_id=%s ORDER BY acquired_month", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_item(user_id, data):
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    data['user_id'] = user_id
    cols = ', '.join(data.keys())
    placeholders = ', '.join(['%s' if is_pg else '?'] * len(data))
    c.execute(f"INSERT INTO items ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


# ==================== Followers CRUD ====================

def get_followers(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM followers WHERE user_id=?", (user_id,))
    except Exception:
        c.execute("SELECT * FROM followers WHERE user_id=%s", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== World CRUD ====================

def get_world(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM world WHERE user_id=?", (user_id,))
    except Exception:
        c.execute("SELECT * FROM world WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_world_faction(user_id, faction_name, influence='中', treasury=0):
    conn = get_db()
    c = conn.cursor()
    try:
        if bool(DATABASE_URL):
            c.execute("INSERT INTO world (user_id, faction_name, influence, treasury) VALUES (%s,%s,%s,%s)",
                      (user_id, faction_name, influence, treasury))
        else:
            c.execute("INSERT INTO world (user_id, faction_name, influence, treasury) VALUES (?,?,?,?)",
                      (user_id, faction_name, influence, treasury))
    except Exception:
        pass
    conn.commit()
    conn.close()


# ==================== NPC批量初始化 ====================

def init_npc_data(user_id, faction):
    """首次创建角色时，初始化该势力NPC到数据库"""
    from .npc_data import get_npcs_by_faction, get_all_npcs
    is_pg = bool(DATABASE_URL)

    if faction == "宋":
        npcs = [n for n in get_all_npcs() if n.get("npc_faction") in ("宋",)]
    else:
        npcs = get_npcs_by_faction(faction)

    conn = get_db()
    c = conn.cursor()
    # 先清理旧数据
    if is_pg:
        c.execute("DELETE FROM npc WHERE user_id=%s", (user_id,))
    else:
        c.execute("DELETE FROM npc WHERE user_id=?", (user_id,))

    for npc in npcs:
        data = {
            "user_id": user_id,
            "name": npc.get("name", ""),
            "bond": npc.get("bond", "寻常"),
            "tags": npc.get("tags", "[]") if isinstance(npc.get("tags"), str) else json.dumps(npc.get("tags", []), ensure_ascii=False),
            "note": npc.get("note", ""),
            "grudge_reason": npc.get("grudge_reason", ""),
            "grudge_level": npc.get("grudge_level", ""),
            "npc_identity": npc.get("npc_identity", ""),
            "npc_official_title": npc.get("npc_official_title", ""),
            "npc_party": npc.get("npc_party", ""),
            "npc_power": npc.get("npc_power", "微末"),
            "npc_faction": npc.get("npc_faction", faction),
            "npc_age": npc.get("npc_age", 30),
            "npc_health": npc.get("npc_health", "康健"),
            "npc_personality": npc.get("npc_personality", "{}") if isinstance(npc.get("npc_personality"), str) else json.dumps(npc.get("npc_personality", {}), ensure_ascii=False),
            "npc_greed": npc.get("npc_greed", "中"),
            "npc_malice": npc.get("npc_malice", "中"),
            "npc_loyalty": npc.get("npc_loyalty", "中"),
            "npc_intelligence": npc.get("npc_intelligence", "普通"),
            "npc_military": npc.get("npc_military", "平庸"),
            "npc_alertness": npc.get("npc_alertness", "中"),
            "is_active": npc.get("is_active", "true"),
            "months_no_interact": npc.get("months_no_interact", 0),
        }
        cols = ', '.join(data.keys())
        ph = ', '.join(['%s' if is_pg else '?'] * len(data))
        c.execute(f"INSERT INTO npc ({cols}) VALUES ({ph})", list(data.values()))

    conn.commit()
    conn.close()
    return len(npcs)


# ==================== 科技研发CRUD ====================

def get_tech_research(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM tech_research WHERE user_id=? ORDER BY category, tech_name", (user_id,))
    except Exception:
        c.execute("SELECT * FROM tech_research WHERE user_id=%s ORDER BY category, tech_name", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def init_tech_research(user_id, tech_names):
    """初始化科技研发记录"""
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    if is_pg:
        c.execute("DELETE FROM tech_research WHERE user_id=%s", (user_id,))
    else:
        c.execute("DELETE FROM tech_research WHERE user_id=?", (user_id,))
    for tech in tech_names:
        try:
            if is_pg:
                c.execute(
                    "INSERT INTO tech_research (user_id, tech_name, category, status, research_points, total_points_required) VALUES (%s,%s,%s,%s,%s,%s)",
                    (user_id, tech['name'], tech['category'], 'locked', 0, tech['cost'])
                )
            else:
                c.execute(
                    "INSERT OR IGNORE INTO tech_research (user_id, tech_name, category, status, research_points, total_points_required) VALUES (?,?,?,?,?,?)",
                    (user_id, tech['name'], tech['category'], 'locked', 0, tech['cost'])
                )
        except Exception:
            pass
    conn.commit()
    conn.close()


def update_tech_research(user_id, tech_name, data):
    conn = get_db()
    c = conn.cursor()
    is_pg = bool(DATABASE_URL)
    fields = []
    values = []
    for k, v in data.items():
        pl = '%s' if is_pg else '?'
        fields.append(f"{k}={pl}")
        values.append(v)
    values.extend([user_id, tech_name])
    c.execute(f"UPDATE tech_research SET {', '.join(fields)} WHERE user_id=%s AND tech_name=%s" if is_pg
              else f"UPDATE tech_research SET {', '.join(fields)} WHERE user_id=? AND tech_name=?", values)
    conn.commit()
    conn.close()


def get_npc_count_for_user(user_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) as cnt FROM npc WHERE user_id=? AND is_active='true'", (user_id,))
    except Exception:
        c.execute("SELECT COUNT(*) as cnt FROM npc WHERE user_id=%s AND is_active='true'", (user_id,))
    row = c.fetchone()
    conn.close()
    return row['cnt'] if row else 0
