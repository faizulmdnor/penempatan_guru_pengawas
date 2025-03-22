import os
import random
import sqlite3

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, url_for, render_template, flash, request, redirect, jsonify
from werkzeug.utils import secure_filename

pengawas = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
pengawas.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
load_dotenv()  # Load variables from .env
pengawas.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_key_here")
ALLOWED_EXTENSIONS = {'csv'}
DB_FILE = 'pengawas_exam.db'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            email TEXT,
            alamat_rumah TEXT,
            poskod TEXT,
            bandar TEXT,
            daerah TEXT,
            nama_sekolah TEXT,
            alamat_sekolah TEXT,
            poskod_sekolah TEXT,
            bandar_sekolah TEXT,
            email_sekolah TEXT,
            nama_pengetua TEXT,
            email_pengetua TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peperiksaan (
            id_exam INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_peperiksaan TEXT,
            tahun_peperiksaan TEXT,
            sesi TEXT,
            start_date TEXT,
            end_date TEXT
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pusat_peperiksaan (
            id_pusat INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pusat TEXT,
            kod_pusat TEXT,
            bilangan_pengawas INTEGER
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guru_pengawas (
            id_gp INTEGER PRIMARY KEY AUTOINCREMENT,
            id_exam INTEGER,
            id_guru INTEGER,
            id_pusat INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_exam) REFERENCES peperiksaan(id_exam),
            FOREIGN KEY (id_guru) REFERENCES guru(id_guru),
            FOREIGN KEY (id_pusat) REFERENCES pusat_peperiksaan(id_pusat)
        );
    ''')

    conn.commit()
    conn.close()


def view_pusat_peperiksaan():
    conn = sqlite3.connect(DB_FILE)
    query_pusat = '''SELECT * FROM pusat_peperiksaan'''

    try:
        data_pusat = pd.read_sql(query_pusat, conn)
    except Exception as e:
        flash(f"Database error: {e}", category='danger')
        data_pusat = pd.DataFrame()
    finally:
        conn.close()
    return data_pusat


def view_details_guru():
    """Retrieved teachers data from guru table."""
    conn = sqlite3.connect(DB_FILE)
    query_guru = '''
        SELECT 
            id_guru,
            nom_kp, 
            firstname, 
            lastname, 
            email, 
            alamat_rumah, 
            nama_sekolah, 
            email_sekolah, 
            nama_pengetua, 
            email_pengetua
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


def view_peperiksaan():
    """Retrieve exam data from peperiksaan table."""
    conn = sqlite3.connect(DB_FILE)
    query_guru = '''
        SELECT *
        FROM peperiksaan
    '''
    try:
        df_exam = pd.read_sql(query_guru, conn)
    except Exception as e:
        flash(message=f"Database error: {e}", category="danger")
        df_exam = pd.DataFrame()
    finally:
        conn.close()
    return df_exam


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


def upload_data_guru(df):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    data = df[['nom_kp', 'firstname', 'lastname', 'email', 'alamat_rumah', 'poskod',
               'bandar', 'daerah', 'nama_sekolah', 'alamat_sekolah', 'poskod_sekolah',
               'bandar_sekolah', 'email_sekolah', 'nama_pengetua', 'email_pengetua']].values.tolist()

    cursor.executemany('''
        INSERT OR IGNORE INTO guru (nom_kp, firstname, lastname, email, alamat_rumah, poskod,
                                    bandar, daerah, nama_sekolah, alamat_sekolah, poskod_sekolah,
                                    bandar_sekolah, email_sekolah, nama_pengetua, email_pengetua)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()


def upload_data_pusatExam(df):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    data = df[['nama_pusat', 'kod_pusat', 'bilangan_pengawas']].values.tolist()
    cursor.executemany('''INSERT OR IGNORE INTO pusat_peperiksaan (nama_pusat, kod_pusat, bilangan_pengawas) 
                VALUES (?, ?, ?)''', data)
    conn.commit()
    conn.close()


@pengawas.route('/')
def home():
    return render_template("index.html")


@pengawas.route('/upload_guru', methods=['GET', 'POST'])
def upload_guru():
    """Muat naik fail CSV dan simpan ke database."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Tiada fail dipilih!", "danger")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash("Tiada fail dipilih!", "danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(pengawas.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                df = pd.read_csv(filepath)
                upload_data_guru(df)
                flash("Data guru berjaya dimuat naik!", "success")
            except Exception as e:
                flash(f"Ralat memproses fail: {e}", "danger")

            return redirect(url_for('upload_guru'))
        else:
            flash("Format fail tidak dibenarkan! Hanya CSV dibenarkan.", "danger")

    return render_template("upload_guru.html")


@pengawas.route('/pengawas_details', methods=['GET'])
def guru_details():
    """Render halaman maklumat guru."""
    try:
        data_guru = view_details_guru()
        if data_guru.empty:
            flash("Tiada rekod guru, sila muat naik.", "warning")
    except Exception as e:
        flash(f"Ralat pangkalan data: {e}", "danger")
        data_guru = pd.DataFrame()
    return render_template("details_pengawas.html", data_guru=data_guru)


@pengawas.route('/tambah_peperiksaan', methods=['GET', 'POST'])
def add_exam():
    if request.method == 'POST':
        try:
            nama_exam = request.form.get('exam_nama')
            tahun_exam = request.form.get('exam_tahun')
            sesi_exam = request.form.get('sesi_exam')
            mula_exam = request.form.get('mula_exam')
            tamat_exam = request.form.get('tamat_exam')

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO peperiksaan (nama_peperiksaan, tahun_peperiksaan, sesi, start_date, end_date) 
                VALUES (?, ?, ?, ?, ?)
            ''', (nama_exam, tahun_exam, sesi_exam, mula_exam, tamat_exam))

            conn.commit()
            conn.close()

            return jsonify({"message": "Peperiksaan berjaya ditambah!"}), 200

        except Exception as e:
            return jsonify({"error": f"Gagal menambah peperiksaan: {str(e)}"}), 500

    return render_template("add_exam.html")


@pengawas.route('/details_exam', methods=['GET'])
def exam_details():
    try:
        details_exam = view_peperiksaan()
        if details_exam.empty:
            flash("Tiada rekod peperiksaan, sila tambah.", "warning")

    except Exception as e:
        flash(f"Ralat pangkalan data: {e}", "danger")
        details_exam = pd.DataFrame()

    return render_template('details_exam.html', data_exam=details_exam)


@pengawas.route('/edit_exam/<int:id_exam>', methods=['GET', 'POST'])
def edit_exam(id_exam):
    conn = sqlite3.connect(DB_FILE)

    if request.method == 'POST':
        nama_peperiksaan = request.form.get('nama_peperiksaan')
        tahun_peperiksaan = request.form.get('tahun_peperiksaan')
        sesi = request.form.get('sesi')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        conn.execute("""
            UPDATE peperiksaan SET 
            nama_peperiksaan = ?, 
            tahun_peperiksaan = ?, 
            sesi = ?, 
            start_date = ?, 
            end_date = ? 
            WHERE id_exam = ?
        """, (nama_peperiksaan, tahun_peperiksaan, sesi, start_date, end_date, id_exam))

        conn.commit()
        conn.close()

        return redirect(url_for('exam_details'))

    # Fetch existing exam data
    exam = conn.execute("SELECT * FROM peperiksaan WHERE id_exam = ?", (id_exam,)).fetchone()
    conn.close()

    exam_list = {
        'id_exam': exam[0],
        'nama_peperiksaan': exam[1],
        'tahun_peperiksaan': exam[2],
        'sesi': exam[3],
        'start_date': exam[4],
        'end_date': exam[5]
    }

    return render_template('edit_exam.html', exam=exam, examlist=exam_list)


@pengawas.route('/upload_pusatExam', methods=['GET', 'POST'])
def upload_pusatExam():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Tiada fail dipilih", "warning")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("Tiada fial dipilih", "warning")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(pengawas.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                df = pd.read_csv(filepath)
                upload_data_pusatExam(df)
                flash("Data pusat peperiksaan berjaya dimuat naik", "success")
            except Exception as e:
                flash(f"Ralat memproses fail: {e}", "danger")
            return redirect(url_for('add_pusat'))
        else:
            flash("Format fail tidak dibenarkan! sila upload file CSV sahaja", "warning")
    return render_template("tambah_pusat_peperiksaan.html")


@pengawas.route('/pusat_peperiksaan', methods=['GET', 'POST'])
def add_pusat():
    sekolah = view_details_guru()
    nama_pusat_exam = sekolah[['nama_sekolah']].drop_duplicates()
    pusat_exam_list = nama_pusat_exam.to_dict(orient='records')
    df_pusat_exam = view_pusat_peperiksaan()

    if request.method == 'POST':
        nama_pusat = request.form.get('nama_pusat')
        kod_pusat = request.form.get('kod_pusat')
        bil_pengawas = request.form.get('bil_pengawas')

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id_pusat from pusat_peperiksaan WHERE nama_pusat = ? AND kod_pusat = ? AND bilangan_pengawas = ?",
                (nama_pusat, kod_pusat, bil_pengawas))
            existing = cursor.fetchone()

            if existing:
                flash(f"Rekod telah wujud, rekod id: {existing[0]}", category='warning')
                return redirect(request.url)

            cursor.execute('''
                INSERT INTO pusat_peperiksaan (nama_pusat, kod_pusat, bilangan_pengawas) VALUES (?, ?, ?)''',
                           (nama_pusat, kod_pusat, bil_pengawas))
            conn.commit()
            flash("Pusat peperiksaan berjaya ditambah!", category='success')
            return redirect(request.url)

        except sqlite3.Error as e:
            flash(f"Ralat pangkalan data: {e}", category='danger')
        finally:
            conn.close()

    return render_template("tambah_pusat_peperiksaan.html", list_pusat_exam=pusat_exam_list,
                           data_pusat_exam=df_pusat_exam)


@pengawas.route('/edit_pusat/<int:id_pusat>', methods=['GET', 'POST'])
def edit_pusat(id_pusat):
    conn = sqlite3.connect(DB_FILE)

    if request.method == 'POST':
        nama_pusat = request.form.get('nama_pusat')
        kod_pusat = request.form.get('kod_pusat')
        bilangan_pengawas = request.form.get('bilangan_pengawas')

        conn.execute('''
            UPDATE pusat_peperiksaan SET
            nama_pusat = ?,
            kod_pusat = ?,
            bilangan_pengawas = ?
            WHERE id_pusat = ?            
        ''', (nama_pusat, kod_pusat, bilangan_pengawas, id_pusat))
        conn.commit()
        conn.close()
        return redirect(url_for('add_pusat'))

    # Fetch existing pusat peperiksaan data
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pusat_peperiksaan WHERE id_pusat = ?", (id_pusat,))
    pusat_exam = cursor.fetchone()
    conn.close()

    pusat_exam_dict = {
        'id_pusat': pusat_exam[0],
        'nama_pusat': pusat_exam[1],
        'kod_pusat': pusat_exam[2],
        'bilangan_pengawas': pusat_exam[3]
    }
    sekolah = view_details_guru()
    nama_pusat_exam = sekolah[['nama_sekolah']].drop_duplicates()
    pusat_exam_list = nama_pusat_exam.to_dict(orient='records')

    return render_template('edit_pusat.html', pusat_exam=pusat_exam_dict, list_pusat_exam=pusat_exam_list)


@pengawas.route('/delete/<int:id_pusat>', methods=['POST'])
def delete_pusat(id_pusat):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pusat_peperiksaan WHERE id_pusat = ?", (id_pusat,))
        conn.commit()
        flash("Pusat telah dipadam", category='success')

    except Exception as e:
        flash(f"pusat tidak berjaya dipadamkan, ralat: {e}", category='warning')

    finally:
        conn.close()

    return redirect(url_for('add_pusat'))


@pengawas.route('/delete/<int:id_exam>', methods=['POST'])
def delete_exam(id_exam):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM peperiksaan WHERE id_exam = ?", (id_exam,))
        conn.commit()
        flash(f"Peperiksaan telah dipadam", category='success')

    except Exception as e:
        flash(f"Peperiksaan tidak berjaya dipadamkan, ralat: {e}", category='warning')

    finally:
        conn.close()

    return redirect(url_for('add_exam'))


@pengawas.route('/penempatan_pengawas', methods=['GET', 'POST'])
def penempatanPengawas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    data_exam = cursor.execute("SELECT * FROM peperiksaan")
    columns = ['id_exam', 'nama_peperiksaan', 'tahun_peperiksaan', 'sesi', 'start_date', 'end_date']
    list_exam = [dict(zip(columns, row)) for row in data_exam]

    df_details_pengawas = pd.DataFrame()

    if request.method == 'POST':
        id_exam = request.form.get('id_exam')

        # Load data from database
        sql_exam = f"SELECT * FROM peperiksaan WHERE id_exam = {id_exam}"
        df_exam = pd.read_sql(sql_exam, conn)

        sql_guru = '''SELECT id_guru, nom_kp, firstname||" "||lastname as Nama, email, 
                    nama_sekolah, email_sekolah, nama_pengetua, email_pengetua
                    FROM guru'''
        df_guru = pd.read_sql(sql_guru, conn)

        sql_pusat = '''SELECT * FROM pusat_peperiksaan'''
        df_pusat = pd.read_sql(sql_pusat, conn)

        # Prepare for assignments
        list_id_guru = df_guru['id_guru'].tolist()
        available_ids = list_id_guru.copy()
        df_assigned_gp = pd.DataFrame(columns=['id_guru', 'id_exam', 'id_pusat'])

        for _, r in df_pusat.iterrows():
            num_pengawas = r['bilangan_pengawas']
            id_pusat = r['id_pusat']
            id_exam = df_exam.iloc[0]['id_exam']

            dff_data = []  # Store assignments as list of dictionaries

            for _ in range(num_pengawas):
                if not available_ids:  # Check if there are still available teachers
                    break

                id_guru_random = random.choice(available_ids)
                dff_data.append({'id_guru': id_guru_random, 'id_exam': id_exam, 'id_pusat': id_pusat})
                available_ids.remove(id_guru_random)  # Remove assigned teacher

                detail_guru = df_guru[df_guru['id_guru'] == id_guru_random].copy()
                details_pusat = df_pusat[df_pusat['id_pusat'] == id_pusat].copy()
                details_exam = df_exam[df_exam['id_exam'] == id_exam].copy()

                detail_guru['dummykey'] = 1
                details_pusat['dummykey'] = 1
                details_exam['dummykey'] = 1

                details_pengawas = detail_guru.merge(details_exam, how='outer', on='dummykey').merge(details_pusat,
                                                                                                how='outer', on='dummykey')
                details_pengawas.drop(columns=['dummykey'], inplace=True)
                df_details_pengawas = pd.concat([df_details_pengawas, details_pengawas])

            # Convert to DataFrame and append
            df_data = pd.DataFrame(dff_data)
            df_assigned_gp = pd.concat([df_assigned_gp, df_data], ignore_index=True)
    df_details_pengawas.reset_index(inplace=True, drop=True)

    return render_template("penempatan_guru_pengawas.html", list_exam=list_exam, pengawas=df_details_pengawas)


if __name__ == '__main__':
    init_db()
    pengawas.run(debug=True, host="0.0.0.0", port=5300)
