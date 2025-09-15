import os
from flask import Flask, render_template_string, request, redirect
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "data/registros.txt")

app = Flask(__name__)

def read_forms():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    forms = []
    for line in lines:
        nome, telefone, whatsapp = line.strip().split(";")
        forms.append({"nome": nome, "telefone": telefone, "whatsapp": whatsapp == "True"})
    return forms

def write_forms(forms):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for c in forms:
            f.write(f"{c['nome']};{c['telefone']};{c['whatsapp']}\n")

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    if request.method == "POST":
        nome = request.form["nome"].strip()
        telefone = request.form["telefone"].strip()
        whatsapp = "whatsapp" in request.form
        if not nome and not telefone:
            error = "Não existe cadastro vazio. Informe nome e telefone."
        elif not nome:
            error = "É obrigatório cadastrar ao menos um nome."
        elif not telefone:
            error = "O contato deve ter um telefone."
        if error:
            forms = read_forms()
            return render_template_string("""
            <html>
            <head>
                <title>Agenda Pessoal</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <style>
                    body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
                    .container { max-width: 900px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
                    h2 { text-align: center; margin-bottom: 25px; }
                    form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; }
                    label { font-weight: bold; }
                    input[type="text"], input[type="tel"] { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
                    .form-row { display: flex; align-items: center; gap: 10px; }
                    .form-actions { display: flex; justify-content: flex-start; gap: 10px; margin-left: 0; }
                    button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
                    button:hover, .icon-btn:hover { background: #1565c0; }
                    table { width: 100%; min-width: 800px; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
                    th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                    th { background: #1976d2; color: #fff; }
                    tr:last-child td { border-bottom: none; }
                    .icon-btn { padding: 6px 10px; font-size: 16px; margin: 0 2px; }
                    .edit { background: #ffa726; }
                    .edit:hover { background: #fb8c00; }
                    .delete { background: #e53935; }
                    .delete:hover { background: #b71c1c; }
                </style>
                <script>
                    window.onload = function() {
                        var form = document.getElementById('cadastroForm');
                        form.onkeydown = function(e) {
                            if (e.key === "Enter") {
                                e.preventDefault();
                                return false;
                            }
                        };
                    };
                </script>
            </head>
            <body>
            <div class="container">
                <h2>Agenda Pessoal</h2>
                {% if error %}
                <div style="color:#e53935; background:#ffeaea; border:1px solid #e53935; padding:10px; margin-bottom:15px; border-radius:5px;">
                    <i class="fa fa-exclamation-triangle"></i> {{error}}
                </div>
                {% endif %}
                <form method="post" id="cadastroForm">
                    <div class="form-row">
                        <label for="nome">Nome:</label>
                        <input type="text" name="nome" id="nome" required value="{{request.form.nome}}">
                    </div>
                    <div class="form-row">
                        <label for="telefone">Telefone:</label>
                        <input type="tel" name="telefone" id="telefone" required value="{{request.form.telefone}}">
                    </div>
                    <div class="form-row">
                        <label for="whatsapp">WhatsApp:</label>
                        <input type="checkbox" name="whatsapp" id="whatsapp" {% if 'whatsapp' in request.form %}checked{% endif %}>
                    </div>
                    <div class="form-actions">
                        <button type="submit"><i class="fa fa-plus"></i> Cadastrar</button>
                    </div>
                </form>
                <h3 style="margin-top:0;">Contatos cadastrados:</h3>
                <table>
                    <tr>
                        <th style="width: 35%;">Nome</th>
                        <th style="width: 25%;">Telefone</th>
                        <th style="width: 15%;">WhatsApp</th>
                        <th style="width: 25%;">Ações</th>
                    </tr>
                    {% for c in forms %}
                    <tr>
                        <td>{{c.nome}}</td>
                        <td>{{c.telefone}}</td>
                        <td>{{'Sim' if c.whatsapp else 'Não'}}</td>
                        <td>
                            <form action="/edit/{{loop.index0}}" method="get" style="display:inline;">
                                <button class="icon-btn edit" title="Editar"><i class="fa fa-pencil-alt"></i></button>
                            </form>
                            <form action="/delete/{{loop.index0}}" method="get" style="display:inline;" onsubmit="return confirm('Confirma exclusão?');">
                                <button class="icon-btn delete" title="Excluir"><i class="fa fa-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            </body>
            </html>
            """, forms=forms, error=error, request=request)
        forms = read_forms()
        forms.append({"nome": nome, "telefone": telefone, "whatsapp": whatsapp})
        write_forms(forms)
        return redirect("/")
    forms = read_forms()
    return render_template_string("""
    <html>
    <head>
        <title>Agenda Pessoal</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .container { max-width: 900px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
            h2 { text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; }
            label { font-weight: bold; }
            input[type="text"], input[type="tel"] { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-start; gap: 10px; margin-left: 0; }
            button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #1565c0; }
            table { width: 100%; min-width: 800px; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
            th, td { padding: 10px; border-bottom: 1px solid #eee; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            th { background: #1976d2; color: #fff; }
            tr:last-child td { border-bottom: none; }
            .icon-btn { padding: 6px 10px; font-size: 16px; margin: 0 2px; }
            .edit { background: #ffa726; }
            .edit:hover { background: #fb8c00; }
            .delete { background: #e53935; }
            .delete:hover { background: #b71c1c; }
        </style>
        <script>
            window.onload = function() {
                var form = document.getElementById('cadastroForm');
                form.onkeydown = function(e) {
                    if (e.key === "Enter") {
                        e.preventDefault();
                        return false;
                    }
                };
            };
        </script>
    </head>
    <body>
    <div class="container">
        <h2>Agenda Pessoal</h2>
        <form method="post" id="cadastroForm">
            <div class="form-row">
                <label for="nome">Nome:</label>
                <input type="text" name="nome" id="nome" required>
            </div>
            <div class="form-row">
                <label for="telefone">Telefone:</label>
                <input type="tel" name="telefone" id="telefone" required>
            </div>
            <div class="form-row">
                <label for="whatsapp">WhatsApp:</label>
                <input type="checkbox" name="whatsapp" id="whatsapp">
            </div>
            <div class="form-actions">
                <button type="submit"><i class="fa fa-plus"></i> Cadastrar</button>
            </div>
        </form>
        <h3 style="margin-top:0;">Contatos cadastrados:</h3>
        <table>
            <tr>
                <th style="width: 35%;">Nome</th>
                <th style="width: 25%;">Telefone</th>
                <th style="width: 15%;">WhatsApp</th>
                <th style="width: 25%;">Ações</th>
            </tr>
            {% for c in forms %}
            <tr>
                <td>{{c.nome}}</td>
                <td>{{c.telefone}}</td>
                <td>{{'Sim' if c.whatsapp else 'Não'}}</td>
                <td>
                    <form action="/edit/{{loop.index0}}" method="get" style="display:inline;">
                        <button class="icon-btn edit" title="Editar"><i class="fa fa-pencil-alt"></i></button>
                    </form>
                    <form action="/delete/{{loop.index0}}" method="get" style="display:inline;" onsubmit="return confirm('Confirma exclusão?');">
                        <button class="icon-btn delete" title="Excluir"><i class="fa fa-trash"></i></button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    </body>
    </html>
    """, forms=forms)

@app.route("/edit/<int:idx>", methods=["GET", "POST"])
def edit(idx):
    forms = read_forms()
    error = ""
    if idx < 0 or idx >= len(forms):
        return "Formulário não encontrado", 404
    if request.method == "POST":
        nome = request.form["nome"].strip()
        telefone = request.form["telefone"].strip()
        whatsapp = "whatsapp" in request.form
        if not nome and not telefone:
            error = "Não existe cadastro vazio. Informe nome e telefone."
        elif not nome:
            error = "É obrigatório cadastrar ao menos um nome."
        elif not telefone:
            error = "O contato deve ter um telefone."
        if error:
            form = {
                "nome": nome,
                "telefone": telefone,
                "whatsapp": whatsapp
            }
            return render_template_string("""
            <html>
            <head>
                <title>Editar Contato</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <style>
                    body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
                    h2 { text-align: center; margin-bottom: 25px; }
                    form { display: flex; flex-direction: column; gap: 12px; }
                    label { font-weight: bold; }
                    input[type="text"], input[type="tel"] { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
                    .form-row { display: flex; align-items: center; gap: 10px; }
                    .form-actions { display: flex; justify-content: flex-end; gap: 10px; }
                    button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
                    button:hover, .icon-btn:hover { background: #1565c0; }
                    .cancel { background: #e0e0e0; color: #333; }
                    .cancel:hover { background: #bdbdbd; }
                </style>
            </head>
            <body>
            <div class="container">
                <h2>Editar Contato</h2>
                {% if error %}
                <div style="color:#e53935; background:#ffeaea; border:1px solid #e53935; padding:10px; margin-bottom:15px; border-radius:5px;">
                    <i class="fa fa-exclamation-triangle"></i> {{error}}
                </div>
                {% endif %}
                <form method="post">
                    <div class="form-row">
                        <label for="nome">Nome:</label>
                        <input type="text" name="nome" id="nome" value="{{form.nome}}" required>
                    </div>
                    <div class="form-row">
                        <label for="telefone">Telefone:</label>
                        <input type="tel" name="telefone" id="telefone" value="{{form.telefone}}" required>
                    </div>
                    <div class="form-row">
                        <label for="whatsapp">WhatsApp:</label>
                        <input type="checkbox" name="whatsapp" id="whatsapp" {% if form.whatsapp %}checked{% endif %}>
                    </div>
                    <div class="form-actions">
                        <button type="submit"><i class="fa fa-save"></i> Salvar</button>
                        <a href="/" class="icon-btn cancel" style="text-decoration:none;"><i class="fa fa-times"></i> Cancelar</a>
                    </div>
                </form>
            </div>
            </body>
            </html>
            """, form=form, error=error)
        forms[idx]["nome"] = nome
        forms[idx]["telefone"] = telefone
        forms[idx]["whatsapp"] = whatsapp
        write_forms(forms)
        return redirect("/")
    form = forms[idx]
    return render_template_string("""
    <html>
    <head>
        <title>Editar Contato</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 40px auto; background: #fff; padding: 30px 60px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
            h2 { text-align: center; margin-bottom: 25px; }
            form { display: flex; flex-direction: column; gap: 12px; }
            label { font-weight: bold; }
            input[type="text"], input[type="tel"] { padding: 7px; border-radius: 5px; border: 1px solid #bbb; width: 100%; }
            .form-row { display: flex; align-items: center; gap: 10px; }
            .form-actions { display: flex; justify-content: flex-end; gap: 10px; }
            button, .icon-btn { background: #1976d2; color: #fff; border: none; border-radius: 5px; padding: 7px 14px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
            button:hover, .icon-btn:hover { background: #1565c0; }
            .cancel { background: #e0e0e0; color: #333; }
            .cancel:hover { background: #bdbdbd; }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>Editar Contato</h2>
        <form method="post">
            <div class="form-row">
                <label for="nome">Nome:</label>
                <input type="text" name="nome" id="nome" value="{{form.nome}}" required>
            </div>
            <div class="form-row">
                <label for="telefone">Telefone:</label>
                <input type="tel" name="telefone" id="telefone" value="{{form.telefone}}" required>
            </div>
            <div class="form-row">
                <label for="whatsapp">WhatsApp:</label>
                <input type="checkbox" name="whatsapp" id="whatsapp" {% if form.whatsapp %}checked{% endif %}>
            </div>
            <div class="form-actions">
                <button type="submit"><i class="fa fa-save"></i> Salvar</button>
                <a href="/" class="icon-btn cancel" style="text-decoration:none;"><i class="fa fa-times"></i> Cancelar</a>
            </div>
        </form>
    </div>
    </body>
    </html>
    """, form=form)

@app.route("/delete/<int:idx>")
def delete(idx):
    forms = read_forms()
    if idx < 0 or idx >= len(forms):
        return "Formulário não encontrado", 404
    forms.pop(idx)
    write_forms(forms)
    return redirect("/")

if __name__ == "__main__":
    print("Iniciando servidor Flask em http://0.0.0.0:5000 ...")
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        print("Verifique se a porta 5000 está livre ou se há outro serviço rodando.")