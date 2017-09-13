from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify



app = Flask(__name__)

@app.route('/'')
def index():

	return render_template('allocation.html', name='world')
	#return jsonify(sharesTraded)

if __name__ == '__main__':
    app.run(debug=True)
