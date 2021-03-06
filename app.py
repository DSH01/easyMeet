from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from time import sleep
import os
from settings import DB_URI, APP_SECRET_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
db = SQLAlchemy(app)

from models import *
import core

# Start core and try login
core.init()
core.google_login_on_start()


@app.route("/")
def index():
	subjects = db.session.query(Subject).all()
	timers = db.session.query(ActiveTimer).all()
	return render_template("index.html", subjects=subjects, timers=timers)


@app.route("/add_subject", methods=['POST'])
def add_subject():
	name = request.form['name']
	url = request.form['url']

	db.session.add(Subject(name, url))
	db.session.commit()
	return redirect(url_for("index"))


@app.route("/delete_subject", methods=['POST'])
def delete_subject():
	s_id = int(request.form['id'])
	subject_to_delete = Subject.query.get(s_id)

	db.session.delete(subject_to_delete)
	db.session.commit()
	return redirect(url_for("index"))


@app.route("/add_timer", methods=['POST'])
def add_timer():
	start_date = request.form['start_date']
	start_time = request.form['start_time']
	end_date = request.form['end_date']
	end_time = request.form['end_time']
	name = request.form.get('subject')

	start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
	end_datetime = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')

	if start_datetime > end_datetime:
		flash("Start time of Meet can not be later than end time!")
		return redirect(url_for('index'))
	elif start_datetime < datetime.now() or end_datetime < datetime.now():
		flash("Time of Meet can not be earlier than current time!")
		return redirect(url_for('index'))

	timer_obj = ActiveTimer(name, start_datetime, end_datetime)
	db.session.add(timer_obj)
	db.session.commit()

	core.add_meet(timer_obj)

	return redirect(url_for("index"))


@app.route("/delete_timer", methods=['POST'])
def delete_timer():
	t_id = int(request.form['id'])
	timer_to_delete = ActiveTimer.query.get(t_id)

	core.cancel_meet(str(t_id))

	db.session.delete(timer_to_delete)
	db.session.commit()
	return redirect(url_for("index"))


@app.route("/logs")
def log():
	logs = open("core.log").read()
	return render_template('log.html', logs=logs)


@app.route('/test')
def test():
	images = sorted([os.path.join(r, n)  for r, _, f in os.walk("static/img/") for n in f])
	return render_template("test.html", images=images)


@app.route('/googlelogin', methods=['GET', 'POST'])
def googlelogin():
	if request.method == 'POST':
		if 'check' in request.form:
			core.screenshot_google_account()

		if 'login' in request.form:
			core.google_login()

			if core.send_mail():
				core.send_password()

		if 'captcha' in request.form:
			captcha_text = request.form['captcha']
			core.send_captcha(captcha_text)
			core.send_password()

		if 'phone_code' in request.form:
			phone_code = request.form['phone_code']
			core.send_phone_code(phone_code)

		if core.check_login():
			core.start_active()

	return render_template("login.html")


if __name__ == '__main__':
	app.run(port=8000, debug=False, use_reloader=False, threaded=True)
