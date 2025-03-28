from flask import Flask, render_template, request, session, redirect, url_for, Response
import Losliste
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

Losliste.current_pilotages()
Losliste.start()

@app.route("/sitemap.xml")
def sitemap():
    cest = datetime.now(tz=pytz.timezone('Europe/Oslo'))
    lastmod = cest.strftime("%Y-%m-%d")
    
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://losliste.no/</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>always</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://losliste.no/karsto</loc>
        <lastmod>{lastmod}</lastmod>
        <changefreq>always</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>'''
    
    return Response(sitemap, mimetype='application/xml')

@app.route("/")
def index():
    dest = request.args.getlist('dest')
    gt = request.args.getlist('gt')
    wx = request.args.getlist('wx')
    std = request.args.getlist('std')
    if not session and len(request.args) == 0:
        session['user'] = True
        navbar = 'show'
        expanded = 'true'
        return redirect("/?dest=mongstad&std=1")
    elif not session:
        session['user'] = True
        navbar = ''
        expanded = 'false'
    elif session and len(request.args) == 0:
        navbar = 'show'
        expanded = 'true'
    elif session and len(request.args) > 0:
        if len(std) == 1:
            navbar = 'show'
            expanded = 'true'
        else:
            navbar = ''
            expanded = 'false'
    if len(gt) == 0:
        gt = ['0']
    update = Losliste.des_query(int(''.join(gt)), tuple(dest))
    result = update[0]
    last_update = update[1]
    errormsg = update[2]
    return render_template('index.html', result=result, last_update=last_update, errormsg=errormsg, dest=dest, gt=gt, wx=wx, navbar=navbar, expanded=expanded)

@app.route("/karsto")
def karsto():
    std = request.args.getlist('std')
    if not session or len(std) == 1:
        session['user'] = True
        navbar = 'show'
        expanded = 'true'
    else:
        navbar = ''
        expanded = 'false'
    dest = request.args.getlist('dest')
    wx = request.args.getlist('wx')
    update = Losliste.karsto_query(tuple(dest))
    result = update[0]
    last_update = update[1]
    errormsg = update[2]
    return render_template('karsto.html', result=result, last_update=last_update, errormsg=errormsg, dest=dest, wx=wx, navbar=navbar, expanded=expanded)

if __name__ == "__main__":
    #Comment out for local testing
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
    #app.run(debug=True, host='0.0.0.0') #Uncomment for local testing
