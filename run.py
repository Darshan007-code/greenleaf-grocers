import os
from app import create_app
from app.database import db

app = create_app(os.getenv('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting GreenLeaf Grocers server on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=debug_mode, use_reloader=False)
