import datetime
from datetime import timedelta

from flask import Flask, jsonify,request
from sqlalchemy import select
from models import UsuarioExemplo, NotasExemplo, db_session
# gerar token
from flask_jwt_extended import create_access_token,  get_jwt_identity,jwt_required, JWTManager
# gerir os papeis
from functools import wraps

# 3jUU

app = Flask(__name__)
# definir a senha, em produção colocar em local seguro
app.config["JWT_SECRET_KEY"] = "morango"
jwt = JWTManager(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f"User:{current_user}")

        try:
            sql = select(UsuarioExemplo).where(UsuarioExemplo.email == current_user)
            usuario_existente =db_session.execute(sql).scalar()
            print(f'Usuario existente: {usuario_existente}')
            if usuario_existente and usuario_existente.papel == "admin":
                return fn(*args, **kwargs)
            dado = {
                "msg":"Acesso negado: Requer privilégio de administrador"
            }
            return jsonify(dado),403
        except Exception as e:
            print("Erro admin_required:",e)
            dado = {
                "msg": "Erro ao verificar privilégio"
            }
            return jsonify(dado), 404
    return wrapper

@app.route('/', methods=['GET'])
def principal():
    dado = {
        "msg": "COD: 3jUU"
    }
    return jsonify(dado), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        print("sdf")
        dados_entrada = request.get_json()
        email = dados_entrada.get('email')
        senha = dados_entrada.get('senha')
        print("email:",email,"senha",senha)

        sql = select(UsuarioExemplo).where(UsuarioExemplo.email == email)
        usuario_existente = db_session.execute(sql).scalar()
        print(f'Usuario existente: {usuario_existente.serialize()}')
        print(f'Senha: {usuario_existente.check_password_hash(senha)}')

        if usuario_existente and usuario_existente.check_password_hash(senha):
            print(datetime.datetime.now())
            access_token = create_access_token(
                identity=str(usuario_existente.email),
                additional_claims={
                    "papel":usuario_existente.papel,
                    "nome":usuario_existente.nome,
                    "criado_em":str(datetime.datetime.now())
                    },
                expires_delta=timedelta(minutes=15)
            )
            dados= {
                "access_token": access_token
            }
            print("UTY:",dados)
            return jsonify(dados),200
        dado = {
            "msg":"Credenciais invalidas"
        }
        return jsonify(dado),401
    except Exception as e:
        return jsonify({"msg": str(e)}), 400

@app.route('/usuarios', methods=['POST'])
def cadastro():
    dados = request.get_json()
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    papel = dados.get('papel','usuario')

    if not nome or not email or not senha:
        return jsonify({"msg": "Email, usuário e senha são obrigatórios"}), 400

    try:
        # Verificar se o usuário já existe
        user_check = select(UsuarioExemplo).where(UsuarioExemplo.email == email)
        usuario_existente = db_session.execute(user_check).scalar()

        if usuario_existente:
            return jsonify({"msg": "Usuário já existe"}), 409

        novo_usuario = UsuarioExemplo(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        db_session.add(novo_usuario)
        db_session.commit()

        user_id = novo_usuario.id
        return jsonify({"msg": "Usuário criado com sucesso", "user_id": user_id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        stmt = select(UsuarioExemplo)
        users_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        users_result = [{"id": user.id, "nome": user.nome} for user in users_result]
        return jsonify(users_result)
    except Exception as e:
        print(str(e))
        dado = {
            "msg": "Credenciais invalidas"
        }
        return jsonify({"msg": f"Erro ao criar nota"}), 500

@app.route('/notas_exemplo', methods=['POST'])
@jwt_required()
def criar_nota_exemplo():
    print("hgk")
    data = request.get_json()
    print("dados_web_criar_tarefa",data)
    conteudo = data.get('conteudo')
    print("conteudo:",conteudo)

    if not conteudo:
        return jsonify({"msg": "Conteúdo da nota é obrigatório"}), 400

    try:
        nova_nota = NotasExemplo(conteudo=conteudo)
        # Se quisesse associar ao usuário: nova_nota.user_id = current_user_id
        db_session.add(nova_nota)
        db_session.commit()
        nota_id = nova_nota.id
        return jsonify({"msg": "Nota criada", "nota_id": nota_id}), 201
    except Exception as e:
        db_session.rollback()
        print(str(e))
        return jsonify({"msg": f"Erro ao criar nota"}), 500

@app.route('/get_nota', methods=['GET'])
def listar_notas_exemplo():

    try:
        stmt = select(NotasExemplo)
        notas_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        notas_list = [{"id": nota.id, "conteudo": nota.conteudo} for nota in notas_result]
        return jsonify(notas_list)
    except Exception as e:
        print(str(e))
        dado = {
            "msg": "Credenciais invalidas"
        }
        return jsonify({"msg": f"Erro ao criar nota"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003, host="0.0.0.0") # Rodar em uma porta diferente da API principal