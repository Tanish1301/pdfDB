from flask import Flask, render_template, request, redirect, make_response
from flask_wtf import FlaskForm
from wtforms import FileField, StringField
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import mysql.connector
import PyPDF2
from io import BytesIO
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Define your MySQL database connection settings
db_config = {
    "user": "admin",  # Replace with your MySQL username
    "password": "password",  # Replace with your MySQL password
    "host": "flaskdb.cl6iirlcqhf1.us-east-1.rds.amazonaws.com",    
    "database": "mydatabase1",  # Replace with your database name
}

# Function to create a database connection
def create_db_connection():
    return mysql.connector.connect(**db_config)

# Connect to the database using the provided configuration
conn = create_db_connection()
cursor = conn.cursor()

# Create the 'pdf_files' table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS pdf_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    data LONGBLOB NOT NULL,
    summary TEXT
)
"""

cursor.execute(create_table_query)
conn.commit()
print("Table 'pdf_files' created successfully")


class PDFUploadForm(FlaskForm):
    pdf_file = FileField("PDF File")
    new_filename = StringField("New Filename")

@app.route("/", methods=["GET", "POST"])
def index():
    form = PDFUploadForm()
    if form.validate_on_submit():
        if request.form.get("upload_to_db"):
            pdf_file = request.files["pdf_file"]

            if pdf_file and pdf_file.filename.endswith(".pdf"):
                new_filename = request.form.get("new_filename")
                summary = request.form.get("summary")

                pdf_file.filename = secure_filename(new_filename + ".pdf")
                pdf_data = pdf_file.read()
                cursor.execute("INSERT INTO pdf_files (name, data, summary) VALUES (%s, %s, %s)", (new_filename, pdf_data, summary))
                conn.commit()
                return redirect("/success")
            else:
                return "Error: Invalid file format. Please upload a PDF file."
        else:
            return "Success: File was not uploaded to the database."
    return render_template("index.html", form=form)

@app.route("/success")
def success():
    cursor.execute("SELECT id, name, summary FROM pdf_files")
    file_names = cursor.fetchall()
    return render_template("success.html", file_names=file_names)

@app.route("/download/<int:file_id>")
def download(file_id):
    cursor.execute("SELECT data FROM pdf_files WHERE id = %s", (file_id,))
    file_data = cursor.fetchone()

    if file_data is None:
        return "Error: File not found."

    response = make_response(file_data[0])
    response.headers["Content-Disposition"] = "attachment; filename=myfile.pdf"
    return response

@app.route("/preview/<int:file_id>")
def preview(file_id):
    cursor.execute("SELECT data FROM pdf_files WHERE id = %s", (file_id,))
    file_data = cursor.fetchone()

    if file_data is None:
        return "Error: File not found."

    response = make_response(file_data[0])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=myfile.pdf'
    return response

@app.route("/delete/<int:file_id>", methods=["POST"])
def delete(file_id):
    cursor.execute("DELETE FROM pdf_files WHERE id = %s", (file_id,))
    conn.commit()
    return redirect("/success")

@app.route("/view_summary/<int:file_id>", methods=["GET"])
def view_summary(file_id):
    cursor.execute("SELECT summary FROM pdf_files WHERE id = %s", (file_id,))
    summary = cursor.fetchone()[0]
    return render_template("view_summary.html", summary=summary)

csrf = CSRFProtect(app)

if __name__ == '__main__':
    app.run(debug=True)
