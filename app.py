from flask import Flask, render_template, redirect, session, flash
from models import db, connect_db, User, Feedback
from forms import RegisterForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///feedback"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "bananas"

connect_db(app)
db.create_all()

@app.route("/")
def homepage():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data

        user = User.register(username, password, first_name, last_name, email)

        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick a different username')
            return render_template('register.html', form=form)
        session['username'] = user.username
        flash('Successfully created your user!', "success")
        return redirect(f"/secret")
    else:
        return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        return redirect(f"/users/{session['username']}")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("login.html", form=form)

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.pop("username")
    return redirect("/login")

@app.route("/users/<username>")
def show_user(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    form = DeleteForm()

    return render_template("show.html", user=user, form=form)


@app.route("/users/<username>/delete", methods=["POST"])
def remove_user(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")
