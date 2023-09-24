from flask import Flask, render_template, url_for
import Losliste

result = Losliste.des_query("mongstad")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html', result=result)

if __name__ == "__main__":
    app.run(debug=True)