from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import mercadopago

app = Flask(__name__)
app.secret_key = "secreto931"

sdk = mercadopago.SDK("APP_USR-8625223623593145-040920-229de533f2cf09c9f8dcf84f97a73b6c-3327435010")

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            senha TEXT,
            status TEXT
        )
    ''')

    # progresso
    c.execute('''
        CREATE TABLE IF NOT EXISTS progresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            aula TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- AULAS ----------------
AULAS = [
    {"id": "aula1", "titulo": "Introdução", "video": "aula1.mp4"},
    {"id": "aula2", "titulo": "Estratégia", "video": "aula2.mp4"},
    {"id": "aula3", "titulo": "Método", "video": "aula3.mp4"}
]

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- REGISTRO ----------------
@app.route('/registrar', methods=['POST'])
def registrar():
    email = request.form['email']
    senha = request.form['senha']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    try:
        c.execute("INSERT INTO usuarios (email, senha, status) VALUES (?, ?, ?)",
                  (email, senha, "pendente"))
        conn.commit()
    except:
        pass

    conn.close()

    return redirect('/comprar?email=' + email)

# ---------------- PAGAMENTO ----------------
@app.route('/comprar')
def comprar():
    email = request.args.get('email')

    preference_data = {
        "items": [{
            "title": "Mini Curso",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": 29.90
        }],
        "payer": {"email": email},
        "back_urls": {
            "success": "https://curso-yvqf.onrender.com/sucesso"
        },
        "auto_return": "approved",
        "notification_url": "https://curso-yvqf.onrender.com/webhook"
    }

    preference = sdk.preference().create(preference_data)
    link = preference["response"]["init_point"]

    return redirect(link)

# ---------------- WEBHOOK ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if "data" in data:
        payment_id = data["data"]["id"]

        payment = sdk.payment().get(payment_id)
        response = payment["response"]

        if response["status"] == "approved":
            email = response["payer"]["email"]

            conn = sqlite3.connect('database.db')
            c = conn.cursor()

            c.execute("UPDATE usuarios SET status='pago' WHERE email=?", (email,))
            conn.commit()
            conn.close()

    return "ok", 200

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = email
            return redirect('/curso')
        else:
            return "Login inválido"

    return render_template('login.html')

# ---------------- CURSO ----------------
@app.route('/curso')
def curso():
    if 'user' not in session:
        return redirect('/login')

    email = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT status FROM usuarios WHERE email=?", (email,))
    status = c.fetchone()

    if not status or status[0] != "pago":
        return "Você ainda não pagou"

    # progresso
    c.execute("SELECT aula FROM progresso WHERE email=?", (email,))
    aulas_vistas = [a[0] for a in c.fetchall()]

    conn.close()

    return render_template('curso.html', aulas=AULAS, vistas=aulas_vistas)

# ---------------- MARCAR AULA ----------------
@app.route('/marcar', methods=['POST'])
def marcar():
    email = session.get('user')
    aula = request.json['aula']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("INSERT INTO progresso (email, aula) VALUES (?, ?)", (email, aula))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT email, status FROM usuarios")
    usuarios = c.fetchall()

    c.execute("SELECT email, COUNT(aula) FROM progresso GROUP BY email")
    progresso = c.fetchall()

    conn.close()

    return render_template('admin.html', usuarios=usuarios, progresso=progresso)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ---------------- SUCESSO ----------------
@app.route('/sucesso')
def sucesso():
    return render_template('sucesso.html')

if __name__ == '__main__':
    app.run(debug=True)