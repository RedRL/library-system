import os
from flask import Flask
from controllers import controllers_bp

app = Flask(__name__)
app.register_blueprint(controllers_bp)

# Get the port from the environment variable, default to 5001 if not set
port = int(os.environ.get("PORT", 5001))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
