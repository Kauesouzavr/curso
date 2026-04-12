from flask import Flask, render_template, request, redirect
import sqlite3
import mercadopago

app = Flask(__name__)

# 🔑 SEU TOKEN AQUI
sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")

# ---------------- BANCO ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            status TEXT,
            payment_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- CRIAR PAGAMENTO ----------------
@app.route('/comprar', methods=['POST'])
def comprar():
    email = request.form['email']

    preference_data = {
        "items": [
            {
                "title": "Mini Curso",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": 29.90
            }
        ],
        "payer": {
            "email": email
        },
        "back_urls": {
            "success": "https://SEU-SITE.onrender.com/sucesso"
        },
        "auto_return": "approved",
        "notification_url": "https://SEU-SITE.onrender.com/webhook"
    }

    preference = sdk.preference().create(preference_data)
    link = preference["response"]["init_point"]

    return redirect(link)

# ---------------- WEBHOOK REAL ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    print("WEBHOOK REAL:", data)

    if "data" in data:
        payment_id = data["data"]["id"]

        payment = sdk.payment().get(payment_id)
        response = payment["response"]

        if response["status"] == "approved":
            email = response["payer"]["email"]

            conn = sqlite3.connect('database.db')
            c = conn.cursor()

            c.execute(
                "INSERT INTO pedidos (email, status, payment_id) VALUES (?, ?, ?)",
                (email, "pago", str(payment_id))
            )

            conn.commit()
            conn.close()

    return "ok", 200


# ---------------- TESTE SEM PAGAR ----------------
@app.route('/teste')
def teste():
    email = request.args.get('email')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO pedidos (email, status, payment_id) VALUES (?, ?, ?)",
        (email, "pago", "TESTE123")
    )

    conn.commit()
    conn.close()

    return f"Pagamento SIMULADO para {email} com sucesso!"


# ---------------- SUCESSO ----------------
@app.route('/sucesso')
def sucesso():
    return render_template('sucesso.html')

# ---------------- CURSO ----------------
@app.route('/curso', methods=['POST'])
def curso():
    email = request.form['email']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM pedidos WHERE email=? AND status='pago'", (email,))
    result = c.fetchone()

    conn.close()

    if result:
        return render_template('curso.html')
    else:
        return "❌ Pagamento não encontrado"

# ---------------- RODAR ----------------
if __name__ == '__main__':
    app.run(debug=True)