from flask import Flask, render_template, request, redirect
import sqlite3
import qrcode
import os
import mercadopago

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
app = Flask(__name__)

# CRIAR BANCO
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        valor REAL,
        status TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# HOME
@app.route('/')
def home():
    return render_template('index.html')

# GERAR PIX
@app.route('/gerar_pix', methods=['POST'])
def gerar_pix():
    nome = request.form['nome']
    valor = float(request.form['valor'])

    payment_data = {
        "transaction_amount": valor,
        "description": "Compra do curso",
        "payment_method_id": "pix",
        "payer": {
            "email": "kauesouzavr@gmail.com",
            "first_name": nome
        }
    }

    payment = sdk.payment().create(payment_data)
    response = payment["response"]

    print(response)

    # Se der erro na API, mostra na tela em vez de quebrar
    if "point_of_interaction" not in response:
        return f"Erro ao gerar PIX:<br><pre>{response}</pre>"

    qr_code = response["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    qr_code_text = response["point_of_interaction"]["transaction_data"]["qr_code"]

    # Salvar pedido no banco
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO pedidos (nome, valor, status) VALUES (?, ?, ?)",
        (nome, valor, "pendente")
    )
    conn.commit()
    conn.close()

    return render_template("pix.html", qr=qr_code, copia=qr_code_text)

# ---------------- PAGAMENTO ----------------
@app.route('/pix')
def pix():
    return render_template('pix.html')

# ---------------- PAINEL ADMIN ----------------
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pedidos")
    pedidos = c.fetchall()
    conn.close()

    return render_template('admin.html', pedidos=pedidos)

# ---------------- CONFIRMAR PAGAMENTO ----------------
@app.route('/confirmar/<int:id>')
def confirmar(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE pedidos SET status='pago' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

# ---------------- RODAR APP ----------------
if __name__ == '__main__':
    app.run(debug=True)