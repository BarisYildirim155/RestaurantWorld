import flask
import flask_login

menuitem_bp = flask.Blueprint("menuitem", __name__)

CATEGORIES = [
    "🥗 Salads & Starters",
    "🍲 Soups",
    "🍝 Pasta & Rice",
    "🍕 Pizza",
    "🥩 Grills & Meat",
    "🐟 Seafood",
    "🍔 Burgers & Sandwiches",
    "🥘 Main Course",
    "🥦 Vegetarian",
    "🍰 Desserts",
    "☕ Hot Drinks",
    "🥤 Cold Drinks",
    "🍞 Sides & Bread",
    "🍺 Beverages",
]

PRICE_RANGES = [
    ("$",   "$ — Budget friendly"),
    ("$$",  "$$ — Mid range"),
    ("$$$", "$$$ — Premium"),
]


class MenuItem:
    def __init__(self, name, description, category, price, price_range, ingredients, allergens, restaurant_num):
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.price_range = price_range
        self.ingredients = ingredients
        self.allergens = allergens
        self.restaurant_num = restaurant_num

    @staticmethod
    def find_by_num(srp, num):
        for m in srp.load_all(MenuItem):
            if m.__oid__.num == num:
                return m
        return None


def get_srp():
    from app import srp
    return srp


@menuitem_bp.route("/restaurant/<int:restaurant_num>/menu/add", methods=["GET", "POST"])
@flask_login.login_required
def add_menu_item(restaurant_num):
    from restaurant import Restaurant
    srp = get_srp()
    restaurant = Restaurant.find_by_num(srp, restaurant_num)
    if not restaurant:
        flask.abort(404)
    if restaurant.owner_username != flask_login.current_user.username:
        flask.abort(403)

    error = None
    if flask.request.method == "POST":
        name        = flask.request.form.get("name", "").strip()
        description = flask.request.form.get("description", "").strip()
        category    = flask.request.form.get("category", "").strip()
        price_str   = flask.request.form.get("price", "").strip()
        price_range = flask.request.form.get("price_range", "$").strip()
        ingredients = flask.request.form.get("ingredients", "").strip()
        allergens   = flask.request.form.get("allergens", "").strip()

        if not name or not category or not price_str:
            error = "Name, category and price are required."
        else:
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                error = "Please enter a valid price."
            else:
                item = MenuItem(name, description, category, price, price_range, ingredients, allergens, restaurant_num)
                srp.save(item)
                flask.flash(f"'{name}' added to the menu.", "success")
                return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))

    return flask.render_template(
        "menuitem_form.html",
        restaurant=restaurant,
        restaurant_num=restaurant_num,
        categories=CATEGORIES,
        price_ranges=PRICE_RANGES,
        error=error
    )


@menuitem_bp.route("/menuitem/<int:num>/edit", methods=["GET", "POST"])
@flask_login.login_required
def edit_menu_item(num):
    from restaurant import Restaurant
    srp = get_srp()
    item = MenuItem.find_by_num(srp, num)
    if not item:
        flask.abort(404)
    restaurant = Restaurant.find_by_num(srp, item.restaurant_num)
    if not restaurant or restaurant.owner_username != flask_login.current_user.username:
        flask.abort(403)

    error = None
    if flask.request.method == "POST":
        name        = flask.request.form.get("name", "").strip()
        description = flask.request.form.get("description", "").strip()
        category    = flask.request.form.get("category", "").strip()
        price_str   = flask.request.form.get("price", "").strip()
        price_range = flask.request.form.get("price_range", "$").strip()
        ingredients = flask.request.form.get("ingredients", "").strip()
        allergens   = flask.request.form.get("allergens", "").strip()

        if not name or not category or not price_str:
            error = "Name, category and price are required."
        else:
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                error = "Please enter a valid price."
            else:
                item.name        = name
                item.description = description
                item.category    = category
                item.price       = price
                item.price_range = price_range
                item.ingredients = ingredients
                item.allergens   = allergens
                srp.save(item)
                flask.flash(f"'{name}' updated.", "success")
                return flask.redirect(
                    flask.url_for("restaurant.detail_restaurant", num=item.restaurant_num))

    return flask.render_template(
        "menuitem_form.html",
        restaurant=restaurant,
        restaurant_num=item.restaurant_num,
        categories=CATEGORIES,
        price_ranges=PRICE_RANGES,
        item=item,
        editing=True,
        error=error
    )


@menuitem_bp.route("/menuitem/<int:num>/delete", methods=["POST"])
@flask_login.login_required
def delete_menu_item(num):
    from restaurant import Restaurant
    srp = get_srp()
    item = MenuItem.find_by_num(srp, num)
    if not item:
        flask.abort(404)
    restaurant = Restaurant.find_by_num(srp, item.restaurant_num)
    if not restaurant or restaurant.owner_username != flask_login.current_user.username:
        flask.abort(403)
    restaurant_num = item.restaurant_num
    srp.delete(item)
    flask.flash("Menu item deleted.", "success")
    return flask.redirect(flask.url_for("restaurant.detail_restaurant", num=restaurant_num))
