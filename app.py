from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for session management

# Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "NIKKI"
}

def get_db_connection():
    """Establish a connection to the MySQL database."""
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor
    )

def format_inr(value):
    """Format numbers as currency in INR."""
    return "\u20b9{:,.0f}".format(value)

# Mock user credentials (can be connected to the database for dynamic management)
USER_CREDENTIALS = {"admin": "password123"}

@app.route("/", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session["user"] = username  # Save user in session
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Dashboard page."""
    if "user" not in session:
        return redirect(url_for("login"))

    predicted_sales = None
    sales_data = []

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Fetch current sales data
                cursor.execute("SELECT month, revenue FROM sales_data ORDER BY id")
                sales_data = cursor.fetchall()

                if request.method == "POST":
                    # Collect data from form
                    month = request.form.get("month")
                    revenue = request.form.get("revenue")

                    # Add new data to sales_data table
                    if month and revenue.isdigit():
                        revenue = int(revenue)
                        cursor.execute("INSERT INTO sales_data (month, revenue) VALUES (%s, %s)", (month, revenue))
                        conn.commit()

                        return redirect(url_for("dashboard"))

                # Predict sales for the next month if sufficient data is available
                if len(sales_data) >= 3:
                    last_revenues = [item["revenue"] for item in sales_data[-3:]]
                    predicted_sales = format_inr(int(sum(last_revenues) / len(last_revenues)))
    except Exception as e:
        print(f"Error accessing the dashboard: {e}")

    return render_template(
        "dashboard.html",
        chart_data=sales_data,
        predicted_sales=predicted_sales,
    )

@app.route("/logout")
def logout():
    """Logout the user."""
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
