from flask import Flask, render_template, request, redirect
import sqlite3
import mercadopago

app = Flask(__name__)

# 🔑 COLOQUE SEU TOKEN AQUI
sdk = mercadopago.SDK("APP_USR-8625223623593145-040920-229de533f2cf09c9f8dcf84f97a73b6c-3327435010")

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
            "success": "https://curso-yvqf.onrender.com/sucesso"
        },
        "auto_return": "approved",
        "notification_url": "https://curso-yvqf.onrender.com/webhook"
    }

    preference = sdk.preference().create(preference_data)

    if "response" not in preference or "init_point" not in preference["response"]:
        return f"Erro ao criar pagamento:<br><pre>{preference}</pre>"

    link = preference["response"]["init_point"]

    return redirect(link)

# ---------------- WEBHOOK ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    print("WEBHOOK:", data)

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

# ---------------- SUCESSO (REDIRECIONA AUTOMÁTICO) ----------------
@app.route('/sucesso')
def sucesso():
    payment_id = request.args.get('payment_id')

    if not payment_id:
        return "Erro no pagamento"

    payment = sdk.payment().get(payment_id)
    response = payment["response"]

    if response["status"] == "approved":
        email = response["payer"]["email"]

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # evita duplicado
        c.execute("SELECT * FROM pedidos WHERE payment_id=?", (payment_id,))
        existe = c.fetchone()

        if not existe:
            c.execute(
                "INSERT INTO pedidos (email, status, payment_id) VALUES (?, ?, ?)",
                (email, "pago", payment_id)
            )
            conn.commit()

        conn.close()

        return redirect(f"/assistir/{payment_id}")

    return "Pagamento não aprovado"

# ---------------- ACESSO DIRETO ----------------
@app.route('/assistir/<payment_id>')
def assistir(payment_id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "SELECT * FROM pedidos WHERE payment_id=? AND status='pago'",
        (payment_id,)
    )

    result = c.fetchone()
    conn.close()

    if result:
        return render_template('curso.html')
    else:
        return "Acesso negado"

# ---------------- TESTE SEM PAGAR ----------------
@app.route('/teste')
def teste():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO pedidos (email, status, payment_id) VALUES (?, ?, ?)",
        ("teste@email.com", "pago", "TESTE123")
    )

    conn.commit()
    conn.close()

    return "Teste criado! Acesse: /assistir/TESTE123"

# ---------------- RODAR ----------------
if __name__ == '__main__':
    app.run(debug=True)