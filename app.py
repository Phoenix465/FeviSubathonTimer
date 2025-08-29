# Imports
from flask import Flask, render_template

# Constants
VERSION = "1.0.0"

# Flask app
app = Flask(__name__)


# Routes
@app.route("/")
def index():
    return render_template("index.html")


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
