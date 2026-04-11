from flask import Flask, render_template, request, redirect
import sqlite3
from flask import session

app = Flask(__name__)

#Senha pra acesso
app.secret_key = "123"  # pode mudar depois

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']

        if senha == "123":  # SUA SENHA
            session['logado'] = True
            return redirect('/curso')
        else:
            return "Senha incorreta"

    return render_template('login.html')


@app.route('/curso')
def curso():
    if not session.get('logado'):
        return redirect('/login')

    return render_template('curso.html')

# CRIAR BANCO
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            valor REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# HOME
@app.route('/')
def home():
    return render_template('index.html')

# BOTÃO COMPRAR -> LINK DO MERCADO PAGO
@app.route('/gerar_pix', methods=['POST'])
def gerar_pix():
    nome = request.form['nome']
    valor = float(request.form['valor'])

    # salvar pedido como pendente
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO pedidos (nome, valor, status) VALUES (?, ?, ?)",
        (nome, valor, "pendente")
    )
    conn.commit()
    conn.close()

    # TROQUE PELO SEU LINK DE PAGAMENTO
    return redirect("https://mpago.la/2hUZRu8")

# PÁGINA PIX (se quiser manter)
@app.route('/pix')
def pix():
    return render_template('pix.html')

# PAINEL ADMIN
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pedidos")
    pedidos = c.fetchall()
    conn.close()

    return render_template('admin.html', pedidos=pedidos)

# CONFIRMAR PAGAMENTO
@app.route('/confirmar/<int:id>')
def confirmar(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE pedidos SET status='pago' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

# RODAR APP
@app.route('/meu-acesso')
def meu_acesso():
    return render_template('curso.html')
if __name__ == '__main__':
    app.run(debug=True)