import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # 默认使用 5001 端口，因为 macOS 的 AirPlay Receiver 可能占用 5000 端口
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)

