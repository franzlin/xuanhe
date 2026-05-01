"""启动脚本"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from api.server import app, init_db

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  《宣和二年》游戏服务器启动")
    print("  访问 http://localhost:5000 开始游戏")
    print("  手机访问：http://<电脑IP>:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
