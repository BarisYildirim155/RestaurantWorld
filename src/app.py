import flask
import flask_login
import sirope

app = flask.Flask(__name__)
app.secret_key = "als-restoran-secret-key-2024"

login_manager = flask_login.LoginManager(app)
login_manager.login_view = "user.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "error"

srp = sirope.Sirope()

from user import user_bp, load_user_by_id
from restaurant import restaurant_bp
from menuitem import menuitem_bp
from review import review_bp
from reservation import reservation_bp

app.register_blueprint(user_bp)
app.register_blueprint(restaurant_bp)
app.register_blueprint(menuitem_bp)
app.register_blueprint(review_bp)
app.register_blueprint(reservation_bp)

@login_manager.user_loader
def load_user(user_id):
    return load_user_by_id(srp, user_id)

@app.route("/")
def index():
    return flask.redirect(flask.url_for("restaurant.list_restaurants"))

@app.errorhandler(404)
def not_found(e):
    return flask.render_template("error.html", code=404, message="Page not found."), 404

@app.errorhandler(403)
def forbidden(e):
    return flask.render_template("error.html", code=403, message="You don't have permission to do that."), 403

@app.errorhandler(500)
def server_error(e):
    return flask.render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

@app.template_filter('mod')
def mod_filter(value, divisor):
    return value % divisor

if __name__ == "__main__":
    app.run(debug=True)
