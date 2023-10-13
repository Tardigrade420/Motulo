from flask import Flask, render_template, request, session, redirect, url_for
import Losliste
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

#Losliste.current_pilotages()
Losliste.start()

@app.route("/")
def index():
    if not session and len(request.args) == 0:
        session['user'] = True
        return redirect("/?dest=mongstad")
    elif not session:
        session['user'] = True
    dest = request.args.getlist('dest')
    gt = request.args.getlist('gt')
    if len(gt) == 0:
        gt = ['0']
    update = Losliste.des_query(int(''.join(gt)), tuple(dest))
    result = update[0]
    last_update = update[1]
    errormsg = update[2]
    print(session)
    return render_template('index.html', result=result, last_update=last_update, errormsg=errormsg, dest=dest, gt=gt)



if __name__ == "__main__":
    #Comment out for local testing
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
    #app.run(debug=True, host='0.0.0.0') #Uncomment for local testing

@app.route('/sort', methods=['POST'])
def sort():
    details = request.form.getlist('options')
    print(details)
    return index()