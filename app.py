from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            valor REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- GERAR PAGAMENTO ----------------
@app.route('/gerar_pix', methods=['POST'])
def gerar_pix():
    nome = request.form['nome']
    email = request.form['email']
    valor = float(request.form['valor'])

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO pedidos (nome, email, valor, status) VALUES (?, ?, ?, ?)",
        (nome, email, valor, "pendente")
    )

    conn.commit()
    conn.close()

    # link do pagamento
    return redirect("https://mpago.la/2hUZRu8")

# ---------------- ACESSAR CURSO ----------------
@app.route('/curso', methods=['POST'])
def curso():
    email = request.form['email']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT status FROM pedidos WHERE email=?", (email,))
    pedido = c.fetchone()

    conn.close()

    if pedido and pedido[0] == "pago":
        return render_template('curso.html')
    else:
        return "❌ Pagamento não encontrado ou ainda não aprovado."

# ---------------- PAINEL ADMIN ----------------
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pedidos")
    pedidos = c.fetchall()
    conn.close()

    return render_template('admin.html', pedidos=pedidos)

# ---------------- CONFIRMAR MANUAL ----------------
@app.route('/confirmar/<int:id>')
def confirmar(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE pedidos SET status='pago' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

# ---------------- ACESSO DIRETO (SEU TESTE) ----------------
@app.route('/meu-acesso')
def meu_acesso():
    return render_template('curso.html')

# ---------------- RODAR ----------------
if __name__ == '__main__':
    app.run(debug=True)