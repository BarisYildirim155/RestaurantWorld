import flask
import flask_login
import datetime

reservation_bp = flask.Blueprint("reservation", __name__)

TIME_SLOTS = [
    "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30", "19:00", "19:30",
    "20:00", "20:30", "21:00", "21:30",
    "22:00", "22:30", "23:00",
]

MONTHS = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]


class Reservation:
    def __init__(self, date, time, guest_count, restaurant_num, username):
        self.date = date
        self.time = time
        self.guest_count = guest_count
        self.restaurant_num = restaurant_num
        self.username = username

    @staticmethod
    def find_by_num(srp, num):
        for res in srp.load_all(Reservation):
            if res.__oid__.num == num:
                return res
        return None

    @staticmethod
    def find_by_restaurant(srp, restaurant_num):
        results = [res for res in srp.load_all(Reservation) if res.restaurant_num == restaurant_num]
        return sorted(results, key=lambda r: (r.date, r.time))


def get_srp():
    from app import srp
    return srp


@reservation_bp.route("/restaurant/<int:restaurant_num>/reserve", methods=["GET", "POST"])
@flask_login.login_required
def add_reservation(restaurant_num):
    from restaurant import Restaurant
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, restaurant_num)
    if not restaurant:
        flask.abort(404)

    # Owner cannot reserve their own restaurant
    if restaurant.owner_username == flask_login.current_user.username:
        flask.flash("You cannot make a reservation at your own restaurant.", "error")
        return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))

    error = None
    selected_day   = ""
    selected_month = ""

    if flask.request.method == "POST":
        day         = flask.request.form.get("day", "").strip()
        month       = flask.request.form.get("month", "").strip()
        time        = flask.request.form.get("time", "").strip()
        guest_count = flask.request.form.get("guest_count", "").strip()

        selected_day, selected_month = day, month

        if not day or not month or not time or not guest_count:
            error = "All fields are required."
        else:
            try:
                guest_count = int(guest_count)
                if guest_count < 1 or guest_count > 20:
                    raise ValueError
            except ValueError:
                error = "Number of guests must be between 1 and 20."

            if not error:
                try:
                    month_name = [m[1] for m in MONTHS][int(month) - 1]
                    date_str = f"{month_name} {int(day)}"  # e.g. "May 28"
                    res = Reservation(date_str, time, guest_count, restaurant_num,
                                      flask_login.current_user.username)
                    srp.save(res)
                    flask.flash("Reservation made successfully!", "success")
                    return flask.redirect(
                        flask.url_for("restaurant.detail_restaurant", num=restaurant_num))
                except (ValueError, IndexError):
                    error = "Invalid date selected."

    return flask.render_template(
        "reservation_form.html",
        restaurant=restaurant,
        restaurant_num=restaurant_num,
        time_slots=TIME_SLOTS,
        months=MONTHS,
        selected_day=selected_day,
        selected_month=selected_month,
        error=error
    )


@reservation_bp.route("/reservation/<int:num>/delete", methods=["POST"])
@flask_login.login_required
def delete_reservation(num):
    srp = get_srp()
    res = Reservation.find_by_num(srp, num)
    if not res:
        flask.abort(404)
    if res.username != flask_login.current_user.username:
        flask.abort(403)

    restaurant_num = res.restaurant_num
    srp.delete(res)
    flask.flash("Reservation cancelled.", "success")
    return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))
