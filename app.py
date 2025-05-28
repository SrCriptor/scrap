from flask import Flask, render_template, request

app = Flask(__name__, static_url_path='/static')

@app.route("/", methods=["GET", "POST"])
def index():
    media_url = None
    if request.method == "POST":
        media_url = request.form.get("media_url")
    return render_template("index.html", media_url=media_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
