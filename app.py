from flask import Flask, render_template, url_for
import Losliste
import time

app = Flask(__name__)


@app.route("/")
def index():
    update = Losliste.des_query("mongstad")
    result = update[0]
    last_update = update[1]
    return render_template('index.html', result=result, last_update=last_update)

if __name__ == "__main__":
    #Comment out for local testing
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=8080)
    #Uncomment for local testing
    app.run(debug=True)
