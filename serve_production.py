import os
import sys
from app import create_app
from app.database import db

# Initialize production app
app = create_app('production')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    print("=" * 65)
    print("[*] GREENLEAF GROCERS - PRODUCTION WSGI SERVER (Waitress)")
    print("=" * 65)
    print(f"• Serving on all interfaces: http://0.0.0.0:{port}")
    print(f"• Local browser access:      http://127.0.0.1:{port}")
    print(f"• LAN / Tablet / Mobile:     http://<YOUR_LOCAL_IP>:{port}")
    print(f"• Multi-threaded workers:    8 threads")
    print(f"• Press CTRL+C to terminate.")
    print("=" * 65)
    serve(app, host='0.0.0.0', port=port, threads=8)
