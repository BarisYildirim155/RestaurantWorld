import flask
import flask_login
import sirope
from werkzeug.security import generate_password_hash, check_password_hash

user_bp = flask.Blueprint("user", __name__)


class User(flask_login.UserMixin):
    def __init__(self, username, password, email, is_owner=False):
        self.username = username
        self.password = password
        self.email = email
        self.is_owner = is_owner

    def get_id(self):
        return self.username

    @property
    def owner(self):
        return getattr(self, 'is_owner', False)

    @staticmethod
    def find(srp, username):
        for user in srp.load_all(User):
            if user.username == username:
                return user
        return None


def load_user_by_id(srp, user_id):
    return User.find(srp, user_id)


def get_srp():
    from app import srp
    return srp


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    error = None
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "").strip()
        email    = flask.request.form.get("email", "").strip()
        password = flask.request.form.get("password", "").strip()
        is_owner = flask.request.form.get("is_owner") == "on"

        if not username or not email or not password:
            error = "All fields are required."
        elif User.find(get_srp(), username):
            error = "This username is already taken."
        else:
            user = User(username, generate_password_hash(password), email, is_owner)
            get_srp().save(user)
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    return flask.render_template("register.html", error=error)


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    error = None
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "").strip()
        password = flask.request.form.get("password", "").strip()
        user = User.find(get_srp(), username)

        if not user or not check_password_hash(user.password, password):
            error = "Invalid username or password."
        else:
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    return flask.render_template("login.html", error=error)


@user_bp.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("user.login"))
