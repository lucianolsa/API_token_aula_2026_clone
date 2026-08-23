import os
from datetime import timedelta, datetime
from flask import Flask, jsonify,request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models import Usuario, db_session, Atividade, Recurso
# gerar token
from flask_jwt_extended import create_access_token,  get_jwt_identity,jwt_required, JWTManager, get_jwt
# gerir os papeis
from functools import wraps
#from supabase import create_client, Client
from dotenv import load_dotenv

# carregar variaveis de ambiente
load_dotenv()

# 3jUU

app = Flask(__name__)
# definir a senha, em produção colocar em local seguro
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
jwt = JWTManager(app)

# previne gargalo "too many connections"
"""
    ### @app.teardown_appcontext (O Zelador)
    ### Para que serve: 
    Fechar conexões de banco de dados, limpar memória temporária, fechar arquivos abertos. 
    Ele evita o temido Memory Leak (Vazamento de Memória).
    ### Curiosidade: 
    Como estamos usando o Flask-SQLAlchemy, você nunca precisará escrever esse comando na mão para o banco de dados. 
    A biblioteca já injeta um teardown_appcontext invisível no seu app que faz db.session.remove() automaticamente.
    """
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f"current_user:{current_user}")

        try:
            sql = select(Usuario).where(Usuario.email == current_user)
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
    print(f"def_identificacaoxx {str(datetime.now())}")
    dados = {
        "msg": "COD: 3jUU",
        "atualizado_em":str(datetime.now())
    }
    return jsonify(dados), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        print("kdr")
        # Tenta ler o JSON sem quebrar o servidor se vier lixo
        dados_entrada = request.get_json(silent=True)
        if not dados_entrada:
            return jsonify({"msg": "JSON inválido"}), 400
        email = dados_entrada.get('email')
        if not email:
            return jsonify({"msg": "Email é obrigatório"}), 400

        # email = dados_entrada.get('email')
        senha = dados_entrada.get('senha')
        print("Login email:",email,"senha",senha)

        sql = select(Usuario).where(Usuario.email == email)
        usuario_existente = db_session.execute(sql).scalar()
        print(f'Usuario existente: {usuario_existente}')
        if not usuario_existente:
            print("'qtd' User not found")
            dados = {
                "msg": "Email não cadastrado"
            }
            return jsonify(dados), 401

        print(f'Usuario existente: {usuario_existente.serialize()}')
        print(f'Senha: {usuario_existente.check_password_hash(senha)}')

        if usuario_existente and usuario_existente.check_password_hash(senha):
            print("datetime.datetime()")
            # criação e configuração token


            '''
            ###create_access_token
            # Prefira SEMPRE colocar o `ID` do banco de dados, não o e-mail. E-mails podem ser alterados pelo usuário no futuro
            * **O que colocar aqui:** Papéis (`roles`), permissões (`permissions`), plano do usuário (ex: `plan: "premium"`).
            * **O que NUNCA colocar aqui:** Senhas, CPF, dados de cartão. Lembre-se: o JWT pode ser lido por qualquer um no site *jwt.io*.

            '''
            access_token = create_access_token(

                identity=str(usuario_existente.id),
                additional_claims={
                    "id":usuario_existente.id,
                    "papel":usuario_existente.papel,
                    "nome":usuario_existente.nome,
                    "criado_em":str(datetime.now())
                    },
                expires_delta=timedelta(minutes=30)
            )
            dados= {
                "access_token": access_token
            }
            print("UTY:",dados)
            return jsonify(dados),200
        dados = {
            "msg":"Credenciais invalidas"
        }
        return jsonify(dados),401
    except Exception as e:
        dados = {
            "msg": "Erro ao logar: str(e)}"
        }
        return jsonify(dados), 400

@app.route('/usuarios', methods=['POST'])
def cadastro():
    print("def_user_post")
    dados = request.get_json()
    print("dados_recebido: ",dados)
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    papel = dados.get('papel','usuario')

    if not nome or not email or not senha:
        dados = {
            "msg": "Email, usuário e senha são obrigatórios"
        }
        return jsonify(dados), 400

    try:
        # Verificar se o usuário já existe
        user_check = select(Usuario).where(Usuario.email == email)
        usuario_existente = db_session.execute(user_check).scalar()

        if usuario_existente:
            dados = {
                "msg": "Usuário já existe"
            }
            return jsonify(dados), 409

        novo_usuario = Usuario(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        db_session.add(novo_usuario)
        db_session.commit()

        dados = {
            "msg": "Usuário criado com sucesso",
            "user_id": novo_usuario.id
        }
        return jsonify(dados), 201
    except Exception as e:
        db_session.rollback()
        print("erro500: ",e)
        dados = {
            "msg": f"Erro ao registrar usuário: {str(e)}"
        }
        return jsonify(dados), 500

@app.route('/usuarios', methods=['GET'])
@jwt_required()
@admin_required
def listar_usuarios():
    print("def_user_get")
    try:
        stmt = select(Usuario)
        users_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        for usuario in users_result:
            print("asd: ",usuario.serialize())
        users_result = [user.serialize() for user in users_result]
        return jsonify(users_result)
    except Exception as e:
        print("listaUserErro:",str(e))
        dados = {
            "msg": "Erro ao listar usuários"
        }
        return jsonify(dados), 500

@app.route('/atividades', methods=['POST'])
@jwt_required()
def criar_atividade_exemplo():
    data = request.get_json()
    nome = data.get('nome')
    if not nome:
        dados = {
            "msg": "Nomear a atividade é obrigatório"
        }
        return jsonify(dados), 400
    try:
        claims = get_jwt()
        usuario_id = claims.get('id')
        # associa a Atividade ao id logado
        nova_atividade = Atividade(nome=nome,pessoa_id=usuario_id)
        db_session.add(nova_atividade)
        db_session.commit()

        atividade_id = nova_atividade.id
        dados = {
            "msg": "Atividade criada",
            "atividade_id": atividade_id
        }
        return jsonify(dados), 201
    except Exception as e:
        db_session.rollback()
        dados = {
            "msg": "Erro ao criar atividade"
        }
        return jsonify(dados), 500

@app.route('/atividades', methods=['GET'])
@jwt_required()
def listar_atividades_exemplo():
    claims = get_jwt()
    token_identifica = get_jwt_identity()
    is_admin = claims.get('papel') == 'admin'
    if not is_admin:
        dados = {
            "msg": "Acesso negado. Você não tem permissão para ver atividades de outro usuário."
        }
        return jsonify(dados), 403
    try:
        stmt = select(Atividade, Usuario).join(Usuario,Atividade.pessoa_id==Usuario.id)
        atividades_result = db_session.execute(stmt).all()#.scalars().all() # .scalars().all() para obter uma lista de objetos

        atividades_list = []
        for atividade, usuario in atividades_result:
            atividades_list.append(
                {
                    "id": atividade.id,
                    "nome": atividade.nome,
                    "criado_em": atividade.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
                    "proprietario_": atividade.pessoa_id,
                    "usuario": usuario.nome
                }
            )


        # notas_list = [{"id": nota.id, "nome": nota.nome, "criado_em":nota.criado_em} for nota in notas_result]
        return jsonify(atividades_list),200
    except Exception as e:
        print(str(e))
        dados = {
            "msg": "Erro ao listar atividades"
        }
        return jsonify(dados), 500

@app.route('/usuario/<id>/atividades', methods=['GET'])
@jwt_required()
def listar_atividades_usuario(id):
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'
    print('Admim?',is_admin,' ',claims.get('papel') )
    print("***",(str(usuario_logado) != str(id)) and not is_admin)

    if (str(usuario_logado) != str(id)) and not is_admin:
        dados = {
            "msg":"Acesso negado. Você não tem permissão para ver atividades de outro usuário."
        }
        return jsonify(dados), 403
    try:
        stmt = select(Atividade).where(Atividade.pessoa_id==id)
        atividades_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        if not atividades_result:
            dados = {
                "msg": f"Não foram encontradas atividades para este usuário."
            }
            return jsonify(dados), 404
        atividades_list = []
        print("atv:",atividades_result)
        for atividade in atividades_result:
            print("atv:",atividade)
            atividades_list.append({"id": atividade.id, "nome": atividade.nome, "criado_em":atividade.criado_em.strftime("%d/%m/%Y %H:%M:%S")})
        #atividades_list = [{"id": nota.id, "nome": nota.nome, "criado_em":nota.criado_em.strftime("%d/%m/%Y %H:%M:%S")} for nota in atividades_result]
        return jsonify(atividades_list)
    except Exception as e:
        print("erro:",str(e))
        dados = {
            "msg": "Erro ao listar atividades"
        }
        return jsonify(dados), 500

@app.route('/recursos', methods=['POST'])
def post_recurso():
    data = request.get_json()
    nome_ = data.get('nome')
    tipo_ = data.get('tipo')
    descricao_ = data.get('descricao')
    if nome_== '' or tipo_ == '' or descricao_ == '':
        dados = {
            "msg": "Nome, tipo e descrição são obrigatórios"
        }
        return jsonify(dados), 400

    dados_recurso = Recurso(nome= nome_, tipo=tipo_, descricao= descricao_)
    try:
        db_session.add(dados_recurso)
        db_session.commit()
        recurso_id = dados_recurso.id
        dados = {
            "msg": "Recurso criado com sucesso!",
            "recurso_id": recurso_id
        }
        return jsonify(dados), 201
    except SQLAlchemyError as e:
        print(f'Erro ao cadastrar recurso: {e}')
        dados = {
            "msg": "Erro no banco ao cadastrar recurso"
        }
        db_session.rollback()
        return jsonify(dados), 500
    except Exception as ex:
        print(f'Erro a ser analisado: {ex}')
        dados = {
            "msg": "Erro ao criar recurso"
        }
        db_session.rollback()
        return jsonify(dados), 500



if __name__ == '__main__':
    app.run(debug=True, port=5003, host="0.0.0.0") # Rodar em uma porta diferente da API principal