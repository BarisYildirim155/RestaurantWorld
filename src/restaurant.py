import flask
import flask_login

restaurant_bp = flask.Blueprint("restaurant", __name__)


class Restaurant:
    def __init__(self, name, cuisine_type, description, owner_username):
        self.name = name
        self.cuisine_type = cuisine_type
        self.description = description
        self.owner_username = owner_username

    @staticmethod
    def find_all(srp):
        return list(srp.load_all(Restaurant))

    @staticmethod
    def find_by_num(srp, num):
        for r in srp.load_all(Restaurant):
            if r.__oid__.num == num:
                return r
        return None


def get_srp():
    from app import srp
    return srp


@restaurant_bp.route("/restaurants")
def list_restaurants():
    from review import Review
    srp = get_srp()

    all_restaurants = Restaurant.find_all(srp)
    all_reviews = list(srp.load_all(Review))

    # Stats
    total_restaurants = len(all_restaurants)
    total_reviews = len(all_reviews)

    # Avg rating per restaurant
    def avg_for(num):
        rvs = [rv.rating for rv in all_reviews if rv.restaurant_num == num]
        return round(sum(rvs) / len(rvs), 1) if rvs else None

    # Filter by cuisine
    selected_cuisine = flask.request.args.get("cuisine", "")
    cuisines = sorted(set(r.cuisine_type for r in all_restaurants))
    if selected_cuisine:
        all_restaurants = [r for r in all_restaurants if r.cuisine_type == selected_cuisine]

    # Sort
    sort = flask.request.args.get("sort", "newest")
    if sort == "rating":
        all_restaurants = sorted(all_restaurants, key=lambda r: avg_for(r.__oid__.num) or 0, reverse=True)
    elif sort == "name":
        all_restaurants = sorted(all_restaurants, key=lambda r: r.name.lower())

    restaurants = [(r, avg_for(r.__oid__.num)) for r in all_restaurants]

    return flask.render_template(
        "restaurant_list.html",
        restaurants=restaurants,
        cuisines=cuisines,
        selected_cuisine=selected_cuisine,
        sort=sort,
        total_restaurants=total_restaurants,
        total_reviews=total_reviews
    )


@restaurant_bp.route("/my-restaurants")
@flask_login.login_required
def my_restaurants():
    srp = get_srp()
    restaurants = [r for r in srp.load_all(Restaurant) if r.owner_username == flask_login.current_user.username]
    if restaurants:
        return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurants[0].__oid__.num))
    flask.flash("You haven't added a restaurant yet.", "error")
    return flask.redirect(flask.url_for("restaurant.new_restaurant"))


@restaurant_bp.route("/restaurant/new", methods=["GET", "POST"])
@flask_login.login_required
def new_restaurant():
    # Check if user is an owner
    if not flask_login.current_user.owner:
        flask.flash("You are not a restaurant owner. Please register as an owner to add restaurants.", "error")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    srp = get_srp()

    # Check if owner already has a restaurant
    existing = [r for r in srp.load_all(Restaurant) if r.owner_username == flask_login.current_user.username]
    if existing:
        flask.flash("You already have a restaurant. Each owner can only add one restaurant.", "error")
        return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=existing[0].__oid__.num))

    error = None
    if flask.request.method == "POST":
        name = flask.request.form.get("name", "").strip()
        cuisine_type = flask.request.form.get("cuisine_type", "").strip()
        description = flask.request.form.get("description", "").strip()

        if not name or not cuisine_type:
            error = "Restaurant name and cuisine type are required."
        else:
            r = Restaurant(name, cuisine_type, description, flask_login.current_user.username)
            srp.save(r)
            flask.flash("Restaurant added successfully.", "success")
            return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    return flask.render_template("restaurant_form.html", restaurant=None, error=error)


@restaurant_bp.route("/restaurant/<int:num>")
def detail_restaurant(num):
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, num)
    if not restaurant:
        flask.abort(404)

    from menuitem import MenuItem
    from review import Review
    from reservation import Reservation

    menu_items = [m for m in srp.load_all(MenuItem) if m.restaurant_num == num]
    reviews = [rv for rv in srp.load_all(Review) if rv.restaurant_num == num]
    reservations = Reservation.find_by_restaurant(srp, num)

    avg_rating = None
    if reviews:
        avg_rating = round(sum(rv.rating for rv in reviews) / len(reviews), 1)

    return flask.render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        num=num,
        menu_items=menu_items,
        reviews=reviews,
        avg_rating=avg_rating,
        reservations=reservations
    )


@restaurant_bp.route("/restaurant/<int:num>/edit", methods=["GET", "POST"])
@flask_login.login_required
def edit_restaurant(num):
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, num)
    if not restaurant:
        flask.abort(404)
    if restaurant.owner_username != flask_login.current_user.username:
        flask.abort(403)

    error = None
    if flask.request.method == "POST":
        name = flask.request.form.get("name", "").strip()
        cuisine_type = flask.request.form.get("cuisine_type", "").strip()
        description = flask.request.form.get("description", "").strip()

        if not name or not cuisine_type:
            error = "Restaurant name and cuisine type are required."
        else:
            restaurant.name = name
            restaurant.cuisine_type = cuisine_type
            restaurant.description = description
            srp.save(restaurant)
            flask.flash("Restaurant updated successfully.", "success")
            return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=num))

    return flask.render_template("restaurant_form.html", restaurant=restaurant, num=num, error=error)


@restaurant_bp.route("/restaurant/<int:num>/delete", methods=["POST"])
@flask_login.login_required
def delete_restaurant(num):
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, num)
    if not restaurant:
        flask.abort(404)
    if restaurant.owner_username != flask_login.current_user.username:
        flask.abort(403)

    from menuitem import MenuItem
    from review import Review
    from reservation import Reservation

    for item in list(srp.load_all(MenuItem)):
        if item.restaurant_num == num:
            srp.delete(item)

    for rv in list(srp.load_all(Review)):
        if rv.restaurant_num == num:
            srp.delete(rv)

    for res in list(srp.load_all(Reservation)):
        if res.restaurant_num == num:
            srp.delete(res)

    srp.delete(restaurant)
    flask.flash("Restaurant deleted.", "success")
    return flask.redirect(flask.url_for("restaurant.list_restaurants"))
