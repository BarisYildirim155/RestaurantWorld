import flask
import flask_login
import datetime

review_bp = flask.Blueprint("review", __name__)


class Review:
    def __init__(self, rating, comment, restaurant_num, username):
        self.rating = rating
        self.comment = comment
        self.restaurant_num = restaurant_num
        self.username = username
        self.date = datetime.date.today().strftime("%d/%m/%Y")

    @staticmethod
    def find_by_num(srp, num):
        for rv in srp.load_all(Review):
            if rv.__oid__.num == num:
                return rv
        return None

    @staticmethod
    def find_by_user_and_restaurant(srp, username, restaurant_num):
        for rv in srp.load_all(Review):
            if rv.username == username and rv.restaurant_num == restaurant_num:
                return rv
        return None


def get_srp():
    from app import srp
    return srp


@review_bp.route("/restaurant/<int:restaurant_num>/review/add", methods=["GET", "POST"])
@flask_login.login_required
def add_review(restaurant_num):
    from restaurant import Restaurant
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, restaurant_num)
    if not restaurant:
        flask.abort(404)

    # Owner cannot review their own restaurant
    if restaurant.owner_username == flask_login.current_user.username:
        flask.flash("You cannot review your own restaurant.", "error")
        return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))

    # If user already has a review, redirect to edit
    existing = Review.find_by_user_and_restaurant(srp, flask_login.current_user.username, restaurant_num)
    if existing:
        return flask.redirect(flask.url_for("review.edit_review", num=existing.__oid__.num))

    error = None
    if flask.request.method == "POST":
        comment = flask.request.form.get("comment", "").strip()
        rating = flask.request.form.get("rating", "").strip()

        if not comment or not rating:
            error = "Review and rating are required."
        else:
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    raise ValueError
            except ValueError:
                error = "Rating must be between 1 and 5."
            else:
                rv = Review(rating, comment, restaurant_num, flask_login.current_user.username)
                srp.save(rv)
                flask.flash("Review submitted successfully.", "success")
                return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))

    return flask.render_template(
        "review_form.html",
        restaurant=restaurant,
        restaurant_num=restaurant_num,
        review=None,
        editing=False,
        error=error
    )


@review_bp.route("/review/<int:num>/edit", methods=["GET", "POST"])
@flask_login.login_required
def edit_review(num):
    from restaurant import Restaurant
    srp = get_srp()
    rv = Review.find_by_num(srp, num)
    if not rv:
        flask.abort(404)
    if rv.username != flask_login.current_user.username:
        flask.abort(403)

    restaurant = Restaurant.find_by_num(srp, rv.restaurant_num)
    if not restaurant:
        flask.abort(404)

    error = None
    if flask.request.method == "POST":
        comment = flask.request.form.get("comment", "").strip()
        rating = flask.request.form.get("rating", "").strip()

        if not comment or not rating:
            error = "Review and rating are required."
        else:
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    raise ValueError
            except ValueError:
                error = "Rating must be between 1 and 5."
            else:
                rv.rating = rating
                rv.comment = comment
                rv.date = datetime.date.today().strftime("%d/%m/%Y")
                srp.save(rv)
                flask.flash("Review updated successfully.", "success")
                return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=rv.restaurant_num))

    return flask.render_template(
        "review_form.html",
        restaurant=restaurant,
        restaurant_num=rv.restaurant_num,
        review=rv,
        editing=True,
        error=error
    )


@review_bp.route("/review/<int:num>/delete", methods=["POST"])
@flask_login.login_required
def delete_review(num):
    from restaurant import Restaurant
    srp = get_srp()
    rv = Review.find_by_num(srp, num)
    if not rv:
        flask.abort(404)
    if rv.username != flask_login.current_user.username:
        flask.abort(403)

    restaurant_num = rv.restaurant_num
    srp.delete(rv)
    flask.flash("Review deleted.", "success")
    return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))
