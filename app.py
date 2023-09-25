from flask import Flask, render_template, url_for
import Losliste

app = Flask(__name__)

@app.route("/")
def index():
    result = Losliste.des_query("mongstad")
    return render_template('index.html', result=result)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
    #Uncomment for testing
    #app.run(debug=True)
