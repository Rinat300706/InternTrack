from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "internships.db"


def init_db():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            location TEXT,
            application_date TEXT,
            status TEXT NOT NULL,
            job_url TEXT,
            notes TEXT
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():

    # Current page
    page = request.args.get("page", 1, type=int)

    # Date sorting
    sort_order = request.args.get("sort", "desc")

    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    # Status filter
    status_filter = request.args.get("status", "All")

    allowed_statuses = [
        "All",
        "Applied",
        "Interview",
        "Offer",
        "Rejected"
    ]

    if status_filter not in allowed_statuses:
        status_filter = "All"

    per_page = 5

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()


    # -------------------------
    # DASHBOARD STATISTICS
    # -------------------------

    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'Interview'
    """)
    interviews = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'Offer'
    """)
    offers = cursor.fetchone()[0]


    # -------------------------
    # FILTERED RESULT COUNT
    # -------------------------

    if status_filter == "All":

        cursor.execute("""
            SELECT COUNT(*)
            FROM applications
        """)

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM applications
            WHERE status = ?
        """, (status_filter,))

    filtered_total = cursor.fetchone()[0]


    # -------------------------
    # PAGINATION
    # -------------------------

    total_pages = (filtered_total + per_page - 1) // per_page

    if total_pages == 0:
        total_pages = 1

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page


    # -------------------------
    # DATE SORTING
    # -------------------------

    if sort_order == "asc":
        order = "ASC"
    else:
        order = "DESC"


    # -------------------------
    # GET APPLICATIONS
    # -------------------------

    if status_filter == "All":

        query = f"""
            SELECT *
            FROM applications
            ORDER BY
                CASE
                    WHEN application_date IS NULL
                    OR application_date = ''
                    THEN 1
                    ELSE 0
                END,
                application_date {order},
                id {order}
            LIMIT ? OFFSET ?
        """

        cursor.execute(
            query,
            (per_page, offset)
        )

    else:

        query = f"""
            SELECT *
            FROM applications
            WHERE status = ?
            ORDER BY
                CASE
                    WHEN application_date IS NULL
                    OR application_date = ''
                    THEN 1
                    ELSE 0
                END,
                application_date {order},
                id {order}
            LIMIT ? OFFSET ?
        """

        cursor.execute(
            query,
            (status_filter, per_page, offset)
        )

    applications = cursor.fetchall()

    connection.close()


    return render_template(
        "index.html",
        applications=applications,
        total=total,
        interviews=interviews,
        offers=offers,
        page=page,
        total_pages=total_pages,
        sort_order=sort_order,
        status_filter=status_filter
    )


@app.route("/add", methods=["GET", "POST"])
def add_application():

    if request.method == "POST":

        company = request.form["company"]
        position = request.form["position"]
        location = request.form["location"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        job_url = request.form["job_url"]
        notes = request.form["notes"]

        connection = sqlite3.connect(DATABASE)
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO applications
            (company, position, location, application_date, status, job_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            company,
            position,
            location,
            application_date,
            status,
            job_url,
            notes
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("home"))

    return render_template("add.html")

@app.route("/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == "POST":

        company = request.form["company"]
        position = request.form["position"]
        location = request.form["location"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        job_url = request.form["job_url"]
        notes = request.form["notes"]

        cursor.execute("""
            UPDATE applications
            SET company = ?,
                position = ?,
                location = ?,
                application_date = ?,
                status = ?,
                job_url = ?,
                notes = ?
            WHERE id = ?
        """, (
            company,
            position,
            location,
            application_date,
            status,
            job_url,
            notes,
            application_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("home"))

    cursor.execute(
        "SELECT * FROM applications WHERE id = ?",
        (application_id,)
    )

    application = cursor.fetchone()

    connection.close()

    return render_template(
        "edit.html",
        application=application
    )

@app.route("/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE id = ?",
        (application_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)