import os
import sqlite3

import pandas as pd
from flask import Flask, render_template, request, flash, url_for, redirect
from werkzeug.utils import secure_filename

# Initialize Flask application
pg_app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'Data/upload')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
pg_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
pg_app.secret_key = 'your_secret_key_here'

# Define database file
DB_FILE = 'penempatan_guru_pengawas.db'


def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guru (
            id_guru INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_kp TEXT UNIQUE,
            firstname TEXT,
            lastname TEXT,
            date_of_birth TEXT,
            email TEXT,
            alamat_rumah TEXT,
            poskod TEXT,
            bandar TEXT,
            daerah TEXT,
            nama_sekolah TEXT,
            alamat_sekolah TEXT,
            poskod_sekolah TEXT,
            bandar_sekolah TEXT,
            email_sekolah TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peperiksaan (
            id_exam INTEGER PRIMARY KEY AUTOINCREMENT,
            tahun_peperiksaan TEXT,
            nama_peperiksaan TEXT  
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guru_pengawas (
            id_gp INTEGER PRIMARY KEY AUTOINCREMENT,
            id_exam INTEGER,
            id_guru INTEGER,
            nama_sekolah_peperiksaan TEXT,
            alamat_sekolah_peperiksaan TEXT,
            FOREIGN KEY (id_exam) REFERENCES peperiksaan(id_exam),
            FOREIGN KEY (id_guru) REFERENCES guru(id_guru)
        );
    ''')

    conn.commit()
    conn.close()


def view_data_penempatan():
    """Retrieve teacher placement data from the database."""
    conn = sqlite3.connect(DB_FILE)
    query = '''
        SELECT * FROM guru_pengawas gp
        LEFT JOIN peperiksaan p ON gp.id_exam = p.id_exam
        LEFT JOIN guru g ON gp.id_guru = g.id_guru
    '''

    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        df = pd.DataFrame()
    finally:
        conn.close()

    return df


def save_to_db(filepath):
    """Save teacher data from CSV to the database."""
    data = pd.read_csv(filepath)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for _, row in data.iterrows():
        cursor.execute('''
            INSERT OR IGNORE INTO guru (nom_kp, firstname, lastname, date_of_birth, email, alamat_rumah, poskod, bandar, daerah, nama_sekolah, alamat_sekolah, poskod_sekolah, bandar_sekolah, email_sekolah)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (row['nom_kp'], row['firstname'], row['lastname'], row['date_of_birth'], row['email'],
                        row['alamat_rumah'], row['poskod'], row['bandar'], row['daerah'], row['nama_sekolah'],
                        row['alamat_sekolah'], row['poskod_sekolah'], row['bandar_sekolah'], row['email_sekolah']))

    conn.commit()
    conn.close()


def view_details_guru():
    """Retrieved teachers data from guru table."""
    conn = sqlite3.connect(DB_FILE)
    query_guru = '''
        SELECT *
        FROM guru
    '''
    try:
        df_guru = pd.read_sql(query_guru, conn)
    except Exception as e:
        flash(message=f"Database error: {e}", category="danger")
        df_guru = pd.DataFrame()
    finally:
        conn.close()

    return df_guru


@pg_app.route('/')
def index():
    """Render the main page with teacher placement data."""
    try:
        data = view_data_penempatan()
        table_html = data.to_html(classes='table table-bordered table-striped', index=False,
                                  escape=False) if not data.empty else "<p>Rekod tidak ditemui.</p>"
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        table_html = "<p>Ralat carian data.</p>"
    return render_template("index.html", table_html=table_html, data=data)

@pg_app.route('/detail_guru')
def guru_details():
    """Render data guru in details guru page"""
    try:
        data_guru = view_details_guru()
        table_guru = data_guru.to_html(classes="table table-bordered table-striped", index=False,
                                       escape=False) if not data_guru.empty else "<p>Tiada record guru, sila upload.</p>"
    except Exception as e:
        flash(message=f"Database error: {e}", category="danger")
        table_guru = "<p>Ralat pangkalan data.</p>"
    return render_template("details_guru.html", table_guru=table_guru, data_guru=data_guru)


@pg_app.route('/upload_teachers_data', methods=['GET', 'POST'])
def upload_teachers_data():
    """Handle file uploads and save teacher data to the database."""
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash("No file part", "danger")
            return redirect(url_for('upload_teachers_data'))

        file = request.files['csv_file']

        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(url_for('upload_teachers_data'))

        if not file.filename.endswith('.csv'):
            flash("Invalid file format. Only CSV files are allowed.", "danger")
            return redirect(url_for('upload_teachers_data'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(pg_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            save_to_db(filepath)
            flash("File successfully uploaded and data saved to database.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error saving to database: {e}", "danger")
            return redirect(url_for('upload_teachers_data'))

    return render_template('upload_teachers_data.html')




if __name__ == '__main__':
    init_db()
    pg_app.run(debug=True, host="0.0.0.0", port=5020)

