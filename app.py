import os
from datetime import timedelta, datetime
from flask import Flask, jsonify,request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
            sql = select(Usuario).where(Usuario.id == current_user)
            usuario_existente =db_session.execute(sql).scalar()
            print(f'Usuario existente: {usuario_existente}')
            #print(f'teste: {usuario_existente.papel == "admin"}')
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
        print("log:/login")
        # Tenta ler o JSON sem quebrar o servidor se vier lixo
        dados_entrada = request.get_json(silent=True)
        if not dados_entrada:
            return jsonify({"msg": "JSON inválido"}), 400
        email = dados_entrada.get('email')
        if not email:
            return jsonify({"msg": "Email é obrigatório"}), 400

        # email = dados_entrada.get('email')
        senha = dados_entrada.get('senha')
        print("log: Login email:",email,"senha",senha)

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

@app.route('/usuarios/<int:id>', methods=['PUT'])
@jwt_required()
def atualizar_usuario(id):
    # --- 1. IDENTIFICAÇÃO E AUTORIZAÇÃO ---
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'

    if str(usuario_logado) != str(id) and not is_admin:
        dados = {"msg": "Acesso negado. Você só pode atualizar o seu próprio perfil."}
        return jsonify(dados), 403

    # --- 2. RECEBENDO OS DADOS (Com silent=True) ---
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "JSON inválido"}), 400

    try:
        # --- 3. BUSCA DO USUÁRIO NO BANCO ---
        usuario = db_session.get(Usuario, id)

        if usuario is None:
            return jsonify({"msg": "Usuário não encontrado."}), 404

        # --- 4. ATUALIZAÇÃO DOS CAMPOS ---

        # Só atualizamos o nome se ele foi enviado no JSON
        if 'nome' in data:
            nome_novo = str(data.get('nome')).strip()
            if nome_novo:
                usuario.nome = nome_novo

        # Troca de Senha
        if 'senha' in data:
            senha_nova = str(data.get('senha')).strip()
            if len(senha_nova) >= 4:
                usuario.set_senha_hash(senha_nova)
            else:
                return jsonify({"msg": "A senha deve ter pelo menos 8 caracteres."}), 400

        # A REGRA DO E-MAIL (Evitar duplicidade)
        if 'email' in data:
            email_novo = str(data.get('email')).strip()

            # Só faz a checagem no banco se ele REALMENTE estiver tentando mudar o e-mail
            if email_novo != usuario.email:
                # Verifica se já existe ALGUÉM com esse e-mail
                email_existente = db_session.execute(
                    select(Usuario).where(Usuario.email == email_novo)
                ).scalar_one_or_none()
                if email_existente:
                    return jsonify({"msg": "O email já está em uso."}), 409 # conflito

                usuario.email = email_novo

        if 'papel' in data:
        # SÓ DEIXAMOS ALTERAR O PAPEL SE QUEM ESTÁ LOGADO FOR UM ADMIN!
            if is_admin:
                usuario.papel = data.get('papel')
            else:
                return jsonify({"msg": "Acesso negado. Apenas administradores podem alterar o papel do usuário."}), 403

        # --- 5. SALVANDO NO BANCO DE DADOS ---
        # Como o objeto 'usuario' está amarrado ao banco, não precisamos de db_session.add(),
        # apenas o commit() já entende que os atributos foram alterados na memória!
        db_session.commit()
        dados = {"msg": "Usuário atualizado com sucesso."}
        return jsonify(dados), 200
    except Exception as e:
        db_session.rollback()
        print("Erro ao atualizar usuário:", str(e))
        dados = {"msg": "Erro interno ao atualizar usuário."}
        return jsonify(dados), 500

@app.route('/usuarios/<int:id>', methods=['GET'])
@jwt_required()
def obter_detalhes_usuario(id):
    # --- 1. IDENTIFICAÇÃO E AUTORIZAÇÃO ---
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'

    # PROTEÇÃO (Somente o dono do perfil ou um Admin podem ver)
    if str(usuario_logado) != str(id) and not is_admin:
        dados = {"msg": "Acesso negado. Você só pode visualizar o seu próprio perfil."}
        return jsonify(dados), 403

    try:
        # --- 2. BUSCA NO BANCO DE DADOS  ---
        usuario = db_session.get(Usuario, id)

        # --- 3. VALIDAÇÃO DE EXISTÊNCIA (404) ---
        if usuario is None:
            return jsonify({"msg": "Usuário não encontrado."}), 404

        # --- 4. MONTAGEM DA RESPOSTA SEGURA ---
        # ATENÇÃO: Repare que o campo 'senha_hash' NÃO está aqui!
        detalhes_usuario = {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "papel": usuario.papel,
            "criado_em": usuario.criado_em.strftime("%d/%m/%Y %H:%M:%S") if usuario.criado_em else None
        }
        return jsonify(detalhes_usuario), 200

    except Exception as e:
        print("Erro ao obter detalhes do usuário:", str(e))
        dados = {"msg": "Erro interno ao buscar detalhes do usuário."}
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
    print("log:token_identifica:",token_identifica)
    is_admin = claims.get('papel') == 'admin'
    if not is_admin:
        atividades_busca = select(Atividade, Usuario).join(Usuario, Atividade.pessoa_id == Usuario.id).where(Atividade.pessoa_id == token_identifica)
        atividades_result = db_session.execute(atividades_busca).all() # .scalars().all() para obter uma lista de objetos
    else:
        stmt = select(Atividade, Usuario).join(Usuario, Atividade.pessoa_id == Usuario.id)
        atividades_result = db_session.execute(stmt).all()  # .scalars().all() # .scalars().all() para obter uma lista de objetos

    try:
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

@app.route('/usuario/<int:id>/atividades', methods=['GET'])
@jwt_required()
def listar_atividades_usuario(id):
    # --- 1. IDENTIFICAÇÃO E AUTORIZAÇÃO ---
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'

    # logs
    print('Admim?',is_admin,' ',claims.get('papel') )
    print("***",(str(usuario_logado) != str(id)) and not is_admin)

    # Se o ID do token for diferente do ID da URL E não for admin, bloqueia.
    if (str(usuario_logado) != str(id)) and not is_admin:
        dados = {
            "msg":"Acesso negado. Você não tem permissão para ver atividades de outro usuário."
        }
        return jsonify(dados), 403
    try:
        # --- 2.  VALIDAÇÃO DO PAI (O USUÁRIO EXISTE?) ---
        # No SQLAlchemy 2.0, usamos db_session.get(Classe, id) para buscar pela Chave Primária
        usuario = db_session.get(Usuario, id)
        if not usuario:
            dados = {
                "msg": "Usuário não encontrado"
            }
            return jsonify(dados), 404

        # --- 3. BUSCA NO BANCO DE DADOS ---
        stmt = select(Atividade).where(Atividade.pessoa_id==id)
        atividades_result = db_session.execute(stmt).scalars().all()  # .scalars().all() para obter uma lista de objetos


        # --- 4. MONTAGEM DA RESPOSTA
        atividades_list = [] # Cria uma lista vazia
        print("log: atv:",atividades_result),0

        for atividade in atividades_result:
            print("intens_atv:",atividade)
            dicionario_atividade = {
                "id": atividade.id,
                "nome": atividade.nome,
                "criado_em": atividade.criado_em.strftime("%d/%m/%Y %H:%M:%S")
            }
            atividades_list.append(dicionario_atividade)
            #atividades_list = [{"id": nota.id, "nome": nota.nome, "criado_em":nota.criado_em.strftime("%d/%m/%Y %H:%M:%S")} for nota in atividades_result]

        return jsonify(atividades_list),200

    except Exception as e:
        print("erro:listar_atividades_usuario:",str(e))
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

@app.route('/atividades/<int:atividade_id>/recursos', methods=['POST'])
@jwt_required()
def add_recursos_em_atividade(atividade_id):
    # --- 1. IDENTIFICAÇÃO DO USUÁRIO LOGADO ---
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'

    # --- 2. VALIDAÇÃO DE ENTRADA (O que o cliente mandou?) ---
    data = request.get_json(silent=True)

    if not data or not data.get('recurso_id'):
        dados = {"msg": "O ID do recurso (recurso_id) é obrigatório."}
        return jsonify(dados), 400

    recurso_id = data.get('recurso_id')

    try:
        # --- 3.VALIDAÇÃO DO PAI (A Atividade existe?) ---
        atividade = db_session.get(Atividade, atividade_id)
        print(f"atividade:{atividade.nome}")

        # --- 4.PROTEÇÃO (A Atividade é desse usuário?) ---
        # Só deixamos adicionar o recurso se o usuário for o dono da atividade ou um Admin
        if str(atividade.pessoa_id) != str(usuario_logado) and not is_admin:
            dados = {"msg": "Acesso negado. Você não tem permissão para adicionar recursos a esta atividade."}
            return jsonify(dados), 403

        # --- 5. VALIDAÇÃO DO FILHO (O Recurso existe?) ---
        recurso = db_session.get(Recurso, recurso_id)
        print(f"recurso:{recurso.nome}")

        if recurso is None:
            dados = {"msg": "Recurso não encontrado."}
            return jsonify(dados), 404

        # --- 6. VALIDAÇÃO DE NEGÓCIO (Evitar Duplicidade) ---
        # Verifica se o recurso já está na lista de recursos desta atividade

        if recurso in atividade.recursos:
            print(f"Recurso {recurso.nome} já está associado à atividade {atividade.nome}.")
            dados = {"msg": "Recurso já adicionado a esta atividade."}
            return jsonify(dados), 409 # 409 = Conflict

        # --- 7. ORM (Salvando no banco) ---
        # O SQLAlchemy faz o INSERT na tabela associativa "atividade_recurso"
        atividade.recursos.append(recurso)
        db_session.commit()
        dados = {
            "msg": "Recurso adicionado à atividade com sucesso!"
        }
        return jsonify(dados), 201

    except Exception as e:
        db_session.rollback()  # Desfaz qualquer alteração pela metade
        print("Erro ao buscar atividade:", str(e))
        dados = {"msg": "Erro interno ao adicionar o recurso."}
        return jsonify(dados), 500

@app.route('/atividade/<int:atividade_id>', methods=['GET'])
@jwt_required()
def get_atividade(atividade_id):

    # --- 1. IDENTIFICAÇÃO E AUTORIZAÇÃO ---
    claims = get_jwt()
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'

    try:
        # --- 2. BUSCA NO BANCO (JOIN com Usuário) ---
        # .options(selectinload...) traz todos os recursos anexados sem travar o banco

        busca_atividade = (
            select(Atividade, Usuario)
            .join(Usuario, Atividade.pessoa_id == Usuario.id)
            .where(Atividade.id == atividade_id)
            .options(selectinload(Atividade.recursos))
        )
        resultado = db_session.execute(busca_atividade).first()

        # --- 3. VALIDAÇÃO DE EXISTÊNCIA (404 Not Found) ---
        # Se a atividade ID 9999 não existir no banco:
        if resultado is None:
            dados = {"msg": "Atividade não encontrada no sistema."}
            return jsonify(dados), 404

        atividade, usuario = resultado


        # ---4. Proteção: só o dono da atividade ou um Admin pode ver os detalhes
        if str(atividade.pessoa_id) != str(usuario_logado) and not is_admin:
            dados = {"msg": "Acesso negado. Você não tem permissão para ver esta atividade."}
            return jsonify(dados), 403

        # --- 5. MONTAGEM DOS RECURSOS
        recursos_list = []

        for recurso in atividade.recursos:
            recursos_list.append(
                {
                    "id": recurso.id,
                    "nome": recurso.nome,
                    "tipo": recurso.tipo,
                    "descricao": recurso.descricao}
            )

        dados = {
            "id": atividade.id,
            "nome": atividade.nome,
            "criado_em": atividade.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
            "proprietario_": {

                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            },
            "recursos": recursos_list,
            "total_recursos": len(recursos_list)
        }
        return jsonify(dados), 200

    except Exception as e:
        print("Erro ao buscar atividade:", str(e))
        dados = {"msg": "Erro interno ao buscar a atividade."}
        return jsonify(dados), 500


if __name__ == '__main__':
    app.run(debug=True, port=5003, host="0.0.0.0") # Rodar em uma porta diferente da API principal