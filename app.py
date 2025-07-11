
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret-key-change-this'

DB = 'database.db'

def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )''')
        c.execute('''CREATE TABLE internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nama_mahasiswa TEXT,
            company TEXT,
            position TEXT,
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()
        conn.close()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        try:
            query_db('INSERT INTO users (name,email,password) VALUES (?,?,?)',(name,email,password))
            flash('Pendaftaran berhasil, silakan login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email sudah terdaftar.')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = query_db('SELECT * FROM users WHERE email=? AND password=?',(email,password),one=True)
        if user:
            session['user'] = dict(user)
            flash('Berhasil masuk.')
            return redirect(url_for('home'))
        flash('Email atau password salah.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    flash('Anda telah logout.')
    return redirect(url_for('home'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user' not in session:
            flash('Silakan login terlebih dahulu.')
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated

@app.route('/input', methods=['GET','POST'])
@login_required
def input_data():
    if request.method == 'POST':
        d = request.form
        query_db('''INSERT INTO internships (user_id, nama_mahasiswa, company, position, start_date, end_date, description)
                    VALUES (?,?,?,?,?,?,?)''',
                 (session['user']['id'], d['nama_mahasiswa'], d['company'], d['position'],
                  d['start_date'], d['end_date'], d['description']))
        flash('Data disimpan')
        return redirect(url_for('list_data'))
    return render_template('input.html')

@app.route('/list')
@login_required
def list_data():
    data = query_db('SELECT * FROM internships WHERE user_id=?',(session['user']['id'],))
    return render_template('list.html', data=[dict(row) for row in data])

@app.route('/detail/<int:id>')
@login_required
def detail_data(id):
    d = query_db('SELECT * FROM internships WHERE id=? AND user_id=?',(id,session['user']['id']),one=True)
    if not d:
        flash('Data tidak ditemukan.')
        return redirect(url_for('list_data'))
    return render_template('detail.html', d=dict(d))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_data(id):
    d = query_db('SELECT * FROM internships WHERE id=? AND user_id=?', (id, session['user']['id']), one=True)
    if not d:
        flash('Data tidak ditemukan atau Anda tidak berhak menghapus.')
    else:
        query_db('DELETE FROM internships WHERE id=?', (id,))
        flash('Data berhasil dihapus.')
    return redirect(url_for('list_data'))


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


