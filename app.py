import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, jsonify, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///main.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():

    #clients avatar
    check_cl = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    if not check_cl:
        return redirect("/client")
    else:
        client_ava = check_cl[0]

    revenues_data = db.execute("SELECT rev_name, rev_ammount,(rev_ammount * 1.0 / (SELECT SUM(rev_ammount) * 1.0 FROM revenues)) * 100 as percentage FROM revenues WHERE user_id = ? ORDER BY rev_ammount DESC", session["user_id"])
    if not revenues_data:
        return redirect("/rev")
    else:
        total_revenue = db.execute("SELECT SUM(rev_ammount) FROM revenues WHERE user_id = ?", session["user_id"])[0]["SUM(rev_ammount)"]
        main_prd_name = db.execute ("SELECT prd_name FROM client WHERE user_id = ?", session["user_id"])[0]['prd_name']
        main_rev = db.execute("SELECT rev_ammount FROM revenues WHERE user_id = ? AND rev_name = ?", session["user_id"], main_prd_name)[0]

    expences_data = db.execute("SELECT exp_name, exp_val,(exp_val * 1.0/ ?) * 100 as percentage FROM exp WHERE user_id = ? ORDER BY exp_val DESC", total_revenue, session["user_id"])
    if not expences_data:
        return redirect("/exp")
    else:
        total_expences = db.execute("SELECT SUM(exp_val) FROM exp WHERE user_id = ?", session["user_id"])[0]["SUM(exp_val)"]
        ebitda = total_revenue - total_expences
        ebitda_sh = (ebitda/total_revenue)*100

    pl_data = db.execute("SELECT value FROM pl WHERE user_id = ? ORDER BY period ASC", session["user_id"])
    if not pl_data:
        return redirect("/plforecast")

    result_year = db.execute("SELECT SUM(value) FROM pl WHERE user_id = ?", session["user_id"])[0]["SUM(value)"]
    form_result_year = abs(db.execute("SELECT SUM(value) FROM pl WHERE user_id = ?", session["user_id"])[0]["SUM(value)"])
    #fill canvas
    canvas_check = db.execute("SELECT * FROM canvas WHERE user_id = ?", session["user_id"])
    if not canvas_check:
        return redirect("/canvas")

    canv = db.execute("SELECT * FROM canvas WHERE user_id = ?", session["user_id"])[0]

    if canv:
        return render_template("index.html", client_ava=client_ava, revenues_data=revenues_data, main_rev=main_rev, expences_data=expences_data, ebitda=ebitda, ebitda_sh=ebitda_sh, pl_data=pl_data, canv=canv, result_year=result_year, form_result_year=form_result_year)
    return render_template("index.html", client_ava=client_ava, revenues_data=revenues_data, main_rev=main_rev, expences_data=expences_data, ebitda=ebitda, ebitda_sh=ebitda_sh, pl_data=pl_data, result_year=result_year, form_result_year=form_result_year)

@app.route("/index_clr", methods=["POST"])
@login_required
def clr():

    if request.method == "POST":
        db.execute("DELETE FROM client WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM revenues WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM exp WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM plmodel WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM pl WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM canvas WHERE user_id = ?", session["user_id"])
        return redirect("/client")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            flash("invalid username and/or password")

        # Remember which user has logged in
        else:
            session["user_id"] = rows[0]["user_id"]
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":


        username = request.form.get("username")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if rows:
            flash("Username already exists")
        else:

            password = request.form.get("password")


            confirmation = request.form.get("confirmation")

            if not password == confirmation:
                flash("password not match")
            else:
                password = generate_password_hash(password)

                db.execute("INSERT INTO users (username, password) VALUES(?, ?)", username, password)

                rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
                session["user_id"] = rows[0]["user_id"]

                return redirect("/")


    return render_template("register.html")

@app.route("/client", methods=["GET", "POST"])
@login_required
def client():
    check_bt = 0
    check_clientdb = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    if check_clientdb:
        check_bt = 1

    if request.method == "POST":
        user_id = session["user_id"]
        cl_ave = 0
        cl_legal = request.form.get("legal")
        cl_private = request.form.get("private")
        cl_status = str(cl_legal) + str(cl_private) #legalprivate displ in db
        cl_product = request.form.get("CLproduct")
        cl_price = request.form.get("CLprice")
        cl_cost = request.form.get("CLcost")
        cl_quantity = request.form.get("CLquantity")
        cl_freq = request.form.get("CLfreq")
        cl_period = request.form.get("period")
        cl_ave = float(cl_price) * float(cl_quantity)
        cl_sales_m = float(cl_ave) * float(cl_freq) * float(cl_period)

        check_bt = 0
        check_clientdb = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
        if check_clientdb:
            db.execute("DELETE FROM client WHERE user_id = ?", session["user_id"])
            db.execute("DELETE FROM revenues WHERE user_id = ?", session["user_id"])
            db.execute("DELETE FROM exp WHERE user_id = ?", session["user_id"])
            db.execute("DELETE FROM plmodel WHERE user_id = ?", session["user_id"])
            db.execute("DELETE FROM pl WHERE user_id = ?", session["user_id"])

        db.execute("INSERT INTO client (user_id, prd_name, prd_price, prd_cost, prd_quantity, prd_frequency, prd_ave_check, prd_sales_month, prd_client_stat) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", user_id, cl_product, cl_price, cl_cost, cl_quantity, cl_freq, cl_ave, cl_sales_m, cl_status)
        return redirect("/rev")

    return render_template("client.html", check_bt = check_bt)


@app.route("/rev", methods=["GET", "POST"])
@login_required
def pl():
    client = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    if not client:
        return redirect("/client")
    client_data = client[0]

    if request.method == "POST":
        cust_qty = request.form.get("cust_qty")
        main_product = client_data["prd_name"]
        main_amount = float(cust_qty) * float(client_data["prd_sales_month"])

        check_rev = db.execute("SELECT * FROM revenues WHERE user_id = ? AND rev_name= ?" , session["user_id"], main_product)
        if check_rev:
            db.execute("DELETE FROM revenues WHERE user_id = ? AND rev_name= ?", session["user_id"], main_product)

        db.execute("INSERT INTO revenues (user_id, rev_name, rev_ammount) VALUES(?, ?, ?)", session["user_id"], main_product, main_amount)
        other_product = request.form.get("other_product")
        #other_value = request.form.get("other_amount")
        other_type = request.form.get("other_type")
        #if other_type == "1":
            #oth_amount = other_value
        #else:
            #oth_amount = float(main_amount) * float(other_value) * 0.01
        #db.execute("INSERT INTO revenues (user_id, rev_name, rev_ammount) VALUES(?, ?, ?)", session["user_id"], other_product, oth_amount)
        return redirect("/")
    return render_template("rev.html")


@app.route("/other_rev", methods=["GET", "POST"])
@login_required
def add():

    if request.method == "POST":

          other_revenues = request.get_json()
          db.execute("INSERT INTO revenues (user_id, rev_name, rev_ammount, rev_type, rev_sh_amount) VALUES(?, ?, ?, ?, ?)", session["user_id"], other_revenues['oth_name'], other_revenues['oth_sales'], other_revenues['oth_select'], other_revenues['oth_sh_amt'] )
    return render_template("pl.html")

#create route for AJAX to get data from DB
@app.route("/client_data", methods=["GET"])
@login_required
def get_client_data():
    client = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    return jsonify(client)


@app.route("/exp", methods=["GET", "POST"])
@login_required
def exp():
    #getting COGS ffrom DB
    client = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    if not client:
        return redirect("/client")
    client_data = client[0]
    cost_ratio = float(client_data["prd_cost"])/(client_data["prd_price"])
    rev = db.execute("SELECT * FROM revenues WHERE user_id = ? AND rev_name = ?", session["user_id"], client_data["prd_name"])
    if not rev:
        return redirect("/rev")
    rev_data = rev[0]
    cogs = float(cost_ratio) * float(rev_data["rev_ammount"])
    sales = rev_data["rev_ammount"]
    product = rev_data["rev_name"]
    db_name = rev_data["rev_name"] + " cost"

    if request.method == "POST":

        check_exp = db.execute("SELECT * FROM exp WHERE user_id = ? AND exp_name= ?" , session["user_id"], db_name)
        if check_exp:
            db.execute("DELETE FROM exp WHERE user_id = ? AND exp_name= ?", session["user_id"], db_name)


        db.execute("INSERT INTO exp (user_id, exp_name, exp_val, exp_sh_amt, exp_type) VALUES(?, ?, ?, ?, ?)", session["user_id"], db_name, cogs, (cost_ratio*100), "%")
        #other_product = request.form.get("other_product")
        #other_type = request.form.get("other_type")
        return redirect("/plforecast")
    return render_template("exp.html", cogs = cogs, sales = sales, product = product)

@app.route("/other_exp", methods=["GET", "POST"])
@login_required
def add_exp():

    if request.method == "POST":

          other_expences = request.get_json()
          db.execute("INSERT INTO exp (user_id, exp_name, exp_val, exp_type, exp_sh_amt) VALUES(?, ?, ?, ?, ?)", session["user_id"], other_expences['oth_name'], other_expences['oth_expences'], other_expences['oth_type'], other_expences['exp_sh_amt'])
    return render_template("exp.html")


@app.route("/plforecast", methods=["GET", "POST"])
@login_required
def plforecast():

    #clients avatar
    client_ch = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])
    if not client_ch:
        return redirect("/client")
    client_ava = db.execute("SELECT * FROM client WHERE user_id = ?", session["user_id"])[0]
    revenues_data = db.execute("SELECT rev_name, rev_ammount,(rev_ammount * 1.0/ (SELECT SUM(rev_ammount) * 1.0 FROM revenues)) * 100 as percentage, rev_type, rev_sh_amount FROM revenues WHERE user_id = ? ORDER BY rev_ammount DESC", session["user_id"])
    if not revenues_data:
        return redirect("/rev")
    total_revenue = db.execute("SELECT SUM(rev_ammount) FROM revenues WHERE user_id = ?", session["user_id"])[0]["SUM(rev_ammount)"]
    expences_data = db.execute("SELECT exp_name, exp_val,(exp_val * 1.0 / ?) * 100 as percentage, exp_type, exp_sh_amt FROM exp WHERE user_id = ? ORDER BY exp_val DESC", total_revenue, session["user_id"])
    if not expences_data:
        return redirect("/exp")
    total_expences = db.execute("SELECT SUM(exp_val) FROM exp WHERE user_id = ?", session["user_id"])[0]["SUM(exp_val)"]
    ebitda = total_revenue - total_expences
    ebitda_sh = (ebitda/total_revenue)*100

    #create ne table for all items
    main_product = client_ava["prd_name"]
    plmodel = db.execute("SELECT * FROM plmodel WHERE user_id = ?", session["user_id"])
    main_rev = db.execute("SELECT rev_ammount FROM revenues WHERE user_id = ? AND rev_name = ?", session["user_id"], main_product)[0]

    #!!!!!!!!!!!! need to update , if add new expences. cause static model pl states
    if not plmodel:
        for rev in revenues_data:

            db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, sh_value) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], rev["rev_name"], rev["rev_ammount"], "1", rev["rev_type"], "1", "0", rev["rev_sh_amount"])

        for exp in expences_data:
            if exp["exp_name"] == main_product:
                db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, sh_value) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], exp["exp_name"], exp["exp_val"], "-1", "%", "1", "0", exp["exp_sh_amt"])
            else:
                db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, sh_value) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], exp["exp_name"], exp["exp_val"], "-1", exp["exp_type"], "1", "0", exp["exp_sh_amt"])



    if request.method == "POST":
        check_plmodel = db.execute("SELECT * FROM plmodel WHERE user_id = ? AND scenario = 'sc1'", session["user_id"])
        if check_plmodel:
            db.execute("DELETE FROM plmodel WHERE user_id = ? AND scenario = 'sc1'", session["user_id"])


        #scenario 1. 10% growth till model (need to put inside function)
        #def scenario1():
        model_data = db.execute("SELECT * FROM plmodel WHERE user_id = ? AND model = '1'", session["user_id"])
        growth_ratio = float(request.form.get("growth_rate"))

        #creates model Pl sales of main product for 12 month
        for data in model_data:
            if data["period"] == 0 and data["side"] == 1 and data["item"] == main_product:
                initial_sales = float(data["value"])/((1 + growth_ratio/100) ** 12)
                db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, scenario) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], data["item"], round(initial_sales, 2), data["side"], data["type"], "0", "1", "sc1")
                for period in range (1, 13):
                    if period != 1:
                        initial_sales = float(data["value"])/((1 + growth_ratio/100) ** (12-(period-1)))
                        db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, scenario) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], data["item"], round(initial_sales,2), data["side"], data["type"], "0", period, "sc1")

        #creates model Pl sales of other products for 12 month
        for data in model_data:
            if data["item"] != main_product and data["type"] == "1" and data["model"] == "1":
                for period in range (1, 13):
                    db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, scenario, sh_value) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], data["item"], data["value"], data["side"], data["type"], "0", period, "sc1", "0")

            if (data["item"] != main_product and data["type"] == "%" and data["model"] == "1") or (data["item"] == main_product and data["side"] == -1 and data["model"] == "1"):
                for period in range (1, 13):
                    main_sales = db.execute("SELECT value FROM plmodel WHERE user_id = ? AND item = ? AND  period = ?", session["user_id"], main_product, period)
                    sales = main_sales[0]["value"]
                    value = float(sales)*float(data["sh_value"])/100
                    db.execute("INSERT INTO plmodel (user_id, item, value, side, type, model, period, scenario, sh_value, share) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], data["item"], round(value, 2), data["side"], data["type"], "0", period, "sc1", data["sh_value"], data["sh_value"])

        for period in range (1, 13):
            pl_by_period = db.execute("SELECT id, item, type, value, sh_value FROM plmodel WHERE user_id = ? AND period = ?", session["user_id"], period)
            tot_rev_h = db.execute("SELECT SUM(value) as rev_sum FROM plmodel WHERE user_id = ? AND side = ? AND  period = ?", session["user_id"], "1", period)
            tot_exp_h = db.execute("SELECT SUM(value) as exp_sum FROM plmodel WHERE user_id = ? AND side = ? AND  period = ?", session["user_id"], "-1", period)
            pl = tot_rev_h[0]["rev_sum"] - tot_exp_h[0]["exp_sum"]

            #### checkin pl table for existing data
            pltest = db.execute("SELECT * FROM pl WHERE user_id = ? AND period = ?", session["user_id"], period)
            if not pltest:
                db.execute("INSERT INTO pl (user_id, scenario, value, period) VALUES(?, ?, ?, ?)", session["user_id"], "sc1", pl, period)
            else:
                db.execute("UPDATE pl SET value = ? WHERE user_id = ? AND period = ?", pl, session["user_id"], period)



            rev_sum_for_per = tot_rev_h[0]["rev_sum"]
            for data in pl_by_period:

                share_from_sales = data["value"]/rev_sum_for_per*100
                id = data["id"]
                db.execute("UPDATE plmodel SET share = ? WHERE id = ? AND user_id = ? AND period = ?", round(share_from_sales, 2), id, session["user_id"], period)

        data_for_table = db.execute("SELECT item, value, share, period FROM plmodel WHERE user_id = ? ORDER BY period ASC", session["user_id"])
        dict_rev ={}
        dict_exp ={}

        #creates dictionary of lists for revenues
        for data in data_for_table:
            items = db.execute("SELECT DISTINCT item, value FROM plmodel WHERE user_id = ? AND period = '0' AND model = '1' AND side = '1' ORDER BY value DESC", session["user_id"])
            for name in items:
                rev_list = []
                row = db.execute("SELECT item, value, period FROM plmodel WHERE user_id = ? AND item = ? AND period != 0", session["user_id"], name["item"])


                for data in row:
                    rev_list.append(data['value'])

                dict_rev[name["item"]] = rev_list

        #creates dictionary of lists for expences
        for data in data_for_table:
            items = db.execute("SELECT DISTINCT item, value FROM plmodel WHERE user_id = ? AND period = '0' AND model = '1' AND side = '-1' ORDER BY value DESC", session["user_id"])
            for name in items:
                exp_list = []
                row = db.execute("SELECT item, value, period FROM plmodel WHERE user_id = ? AND item = ? AND period != 0", session["user_id"], name["item"])


                for data in row:
                    exp_list.append(data['value'])

                dict_exp[name["item"]] = exp_list

        #creates dictionary for pl
        dict_pl = db.execute("SELECT value FROM pl WHERE user_id = ? AND scenario = 'sc1' ORDER BY period ASC", session["user_id"])
        return render_template("plforecast.html", client_ava=client_ava, main_rev=main_rev, revenues_data=revenues_data, expences_data=expences_data, ebitda=ebitda, ebitda_sh=ebitda_sh,  dict_rev=dict_rev, dict_exp=dict_exp, dict_pl=dict_pl )



    return render_template("plforecast.html", client_ava=client_ava, main_rev=main_rev, revenues_data=revenues_data, expences_data=expences_data, ebitda=ebitda, ebitda_sh=ebitda_sh )


@app.route("/canvas", methods=["GET", "POST"])
@login_required
def canvas():
    if request.method == "POST":
        partners = request.form.get("partners")
        activities = request.form.get("activities")
        resources = request.form.get("resources")

        propositions = request.form.get("propositions")
        relationships = request.form.get("relationships")
        channels = request.form.get("channels")

        segments = request.form.get("segments")
        cost_structure = request.form.get("structure")
        rev_streams = request.form.get("streams")

        check_canv = db.execute("SELECT * FROM canvas WHERE user_id = ?", session["user_id"])
        if check_canv:
            db.execute("DELETE FROM canvas WHERE user_id = ?", session["user_id"])

        db.execute("INSERT INTO canvas (user_id, partners, activities, resources, propositions, relationships, channels, segments, cost_structure, rev_streams) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], partners, activities, resources, propositions, relationships, channels, segments, cost_structure, rev_streams)

        return redirect("/")

    return render_template("canvas.html")
