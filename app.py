from flask import Flask, jsonify,request
from sqlalchemy import select
from models import UsuarioExemplo, NotasExemplo, SessionLocalExemplo
# gerar token
from flask_jwt_extended import create_access_token,  get_jwt_identity,jwt_required, JWTManager
# gerir os papeis
from functools import wraps

app = Flask(__name__)
# definir a senha, em produção colocar em local seguro
app.config["JWT_SECRET_KEY"] = "morango"
jwt = JWTManager(app)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f"User:{current_user}")

        db = SessionLocalExemplo()
        try:
            sql = select(UsuarioExemplo).where(UsuarioExemplo.email == current_user)
            usuario_existente = db.execute(sql).scalar()
            print(f'Usuario existente: {usuario_existente}')
            if usuario_existente and usuario_existente.papel == "admin":
                return fn(*args, **kwargs)
            dado = {
                "msg":"Acesso negado: Requer privilégio de administrador"
            }
            return jsonify(dado),403
        finally:
            db.close()
    return wrapper

@app.route('/login', methods=['POST'])
def login():
    try:
        dados_entrada = request.get_json()
        email = dados_entrada.get('email')
        senha = dados_entrada.get('senha')

        db = SessionLocalExemplo()
        sql = select(UsuarioExemplo).where(UsuarioExemplo.email == email)
        usuario_existente = db.execute(sql).scalar()

        if usuario_existente and usuario_existente.check_password(senha):
            access_token = create_access_token(identity=str(usuario_existente.email))
            dados= {
                "access_token": access_token,
                "papel": usuario_existente.papel
            }
            return jsonify(dados),200
        dado = {
            "msg":"Credenciais invalidas"
        }
        return jsonify(dado),401
    except Exception as e:
        return jsonify({"msg": str(e)}), 400
    finally:
        db.close()





@app.route('/cadastro', methods=['POST'])
def cadastro():
    dados = request.get_json()
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    papel = dados.get('papel','usuario')

    if not nome or not email or not senha:
        return jsonify({"msg": "Email, usuário e senha são obrigatórios"}), 400

    db = SessionLocalExemplo()
    try:
        # Verificar se o usuário já existe
        user_check = select(UsuarioExemplo).where(UsuarioExemplo.email == email)
        usuario_existente = db.execute(user_check).scalar()

        if usuario_existente:
            return jsonify({"msg": "Usuário já existe"}), 409

        novo_usuario = UsuarioExemplo(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        db.add(novo_usuario)
        db.commit()

        user_id = novo_usuario.id
        return jsonify({"msg": "Usuário criado com sucesso", "user_id": user_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/notas_exemplo', methods=['POST'])
@jwt_required()
def criar_nota_exemplo():
    data = request.get_json()
    conteudo = data.get('conteudo')

    if not conteudo:
        return jsonify({"msg": "Conteúdo da nota é obrigatório"}), 400

    db = SessionLocalExemplo()
    try:
        nova_nota = NotasExemplo(conteudo=conteudo)
        # Se quisesse associar ao usuário: nova_nota.user_id = current_user_id
        db.add(nova_nota)
        db.commit()
        nota_id = nova_nota.id
        return jsonify({"msg": "Nota criada", "nota_id": nota_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"msg": f"Erro ao criar nota: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/notas_exemplo', methods=['GET'])
def listar_notas_exemplo():
    db = SessionLocalExemplo()
    try:
        stmt = select(NotasExemplo)
        notas_result = db.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        notas_list = [{"id": nota.id, "conteudo": nota.conteudo} for nota in notas_result]
        return jsonify(notas_list)
    finally:
        db.close()



if __name__ == '__main__':
    app.run(debug=True, port=5001, host="0.0.0.0") # Rodar em uma porta diferente da API principal