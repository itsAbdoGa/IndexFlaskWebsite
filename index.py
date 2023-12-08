from flask import Flask,render_template

app= Flask(__name__)
@app.route('/home')
@app.route('/')
def index():
    return render_template('index.html',title = 'Welcome')


app.run(debug=True)
