import datetime
from datetime import timedelta
from flask import Flask, jsonify,request
from sqlalchemy import select
from models import Usuario, db_session, Atividade
# gerar token
from flask_jwt_extended import create_access_token,  get_jwt_identity,jwt_required, JWTManager, get_jwt
# gerir os papeis
from functools import wraps
#from supabase import create_client, Client
from dotenv import load_dotenv


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
    print("def_identificacao")
    dado = {
        "msg": "COD: 3jUU"
    }
    return jsonify(dado), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        print("def_login", datetime.datetime.now())
        dados_entrada = request.get_json()
        email = dados_entrada.get('email')
        senha = dados_entrada.get('senha')
        print("email:",email,"senha",senha)

        sql = select(Usuario).where(Usuario.email == email)
        usuario_existente = db_session.execute(sql).scalar()
        print(f'Usuario existente: {usuario_existente}')
        if not usuario_existente:
            print("qtp")
            dado = {
                "msg": "Email não cadastrado"
            }
            return jsonify(dado), 401

        print(f'Usuario existente: {usuario_existente.serialize()}')
        print(f'Senha: {usuario_existente.check_password_hash(senha)}')
        print("bsa",usuario_existente)
        if usuario_existente and usuario_existente.check_password_hash(senha):
            print(datetime.datetime.now())
            access_token = create_access_token(
                identity=str(usuario_existente.email),
                additional_claims={
                    "id":usuario_existente.id,
                    "papel":usuario_existente.papel,
                    "nome":usuario_existente.nome,
                    "criado_em":str(datetime.datetime.now())
                    },
                expires_delta=timedelta(minutes=30)
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
    print("def_user_post")
    dados = request.get_json()
    print("dados_recebido: ",dados)
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    papel = dados.get('papel','usuario')

    if not nome or not email or not senha:
        return jsonify({"msg": "Email, usuário e senha são obrigatórios"}), 400

    try:
        # Verificar se o usuário já existe
        user_check = select(Usuario).where(Usuario.email == email)
        usuario_existente = db_session.execute(user_check).scalar()

        if usuario_existente:
            return jsonify({"msg": "Usuário já existe"}), 409

        novo_usuario = Usuario(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        db_session.add(novo_usuario)
        db_session.commit()

        user_id = novo_usuario.id
        return jsonify({"msg": "Usuário criado com sucesso", "user_id": user_id}), 201
    except Exception as e:
        db_session.rollback()
        print("erro500: ",e)
        return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    print("def_user_get")
    try:
        stmt = select(Usuario)
        users_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        for usuario in users_result:
            print("asd: ",usuario.serialize())
        users_result = [
            user.serialize() for user in users_result]
        return jsonify(users_result)
    except Exception as e:
        print(str(e))
        dado = {
            "msg": "Credenciais invalidas"
        }
        return jsonify({"msg": f"Erro ao criar nota"}), 500

@app.route('/atividades', methods=['POST'])
@jwt_required()
def criar_nota_exemplo():
    print("def_nota_post")
    data = request.get_json()
    print("dados_web_criar_tarefa",data)
    nome = data.get('nome')
    usuario = data.get('usuario_id')
    print("nome_ativ:",nome)

    if not nome:
        return jsonify({"msg": "Conteúdo da nota é obrigatório"}), 400

    try:
        nova_nota = Atividade(nome=nome,pessoa_id=usuario)
        # Se quisesse associar ao usuário: nova_nota.user_id = current_user_id
        db_session.add(nova_nota)
        db_session.commit()
        nota_id = nova_nota.id
        return jsonify({"msg": "Nota criada", "nota_id": nota_id}), 201
    except Exception as e:
        db_session.rollback()
        print(str(e))
        return jsonify({"msg": f"Erro ao criar nota"}), 500

@app.route('/atividades', methods=['GET'])
@jwt_required()
def listar_notas_exemplo():
    print("def_get_nota")
    claims = get_jwt()
    print("claims:", claims)
    is_admin = claims.get('papel') == 'admin'
    print( "is_admin:", is_admin)
    if not is_admin:
        dados = {
            "msg": "Acesso negado. Você não tem permissão para ver atividades de outro usuário."
        }
        return jsonify(dados), 403
    try:
        stmt = select(Atividade)
        notas_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        notas_list = [{"id": nota.id, "nome": nota.nome, "criado_em":nota.criado_em} for nota in notas_result]
        return jsonify(notas_list),200
    except Exception as e:
        print(str(e))
        dado = {
            "msg": "Credenciais invalidas"
        }
        return jsonify({"msg": f"Erro ao criar nota"}), 500


@app.route('/usuario/<id>/atividades', methods=['GET'])
@jwt_required()
def listar_notas_usuario(id):
    print("def_get_nota_usuario")
    claims = get_jwt()
    print("claims:", claims)
    usuario_logado = claims.get('id')
    is_admin = claims.get('papel') == 'admin'
    print("usuario_logado:",usuario_logado,"is_admin:",is_admin)
    if (str(usuario_logado) != str(id)) or is_admin:
        dados = {
            "msg":"Acesso negado. Você não tem permissão para ver atividades de outro usuário."
        }
        return jsonify(dados), 403
    try:
        stmt = select(Atividade).where(Atividade.pessoa_id==id)
        notas_result = db_session.execute(stmt).scalars().all() # .scalars().all() para obter uma lista de objetos
        notas_list = [{"id": nota.id, "nome": nota.nome, "criado_em":nota.criado_em} for nota in notas_result]
        print("notas_usuario:",notas_list)
        return jsonify(notas_list)
    except Exception as e:
        print(str(e))
        dado = {
            "msg": "Credenciais invalidas"
        }
        return jsonify({"msg": f"Erro ao listar nota"}), 500
@app.route('/recursos', methods=['POST'])
def post_recurso():
    if request.method == 'POST':
        nome_ = request.form.get('form_nome')
        tipo_ = request.form.get('form_tipo')
        descricao_ = request.form.get('form_desc')
        if nome_== '':
            flash("Preencha o nome", "error")
            return render_template('criar_recurso.html')
        if tipo_ == '':
            flash("Preencha o sobrenome", "error")
            return render_template('criar_recurso.html')
        if descricao_ == '':
            flash("Preencha o cpf", "error")
            return render_template('criar_recurso.html')
        dados_pessoa = Recurso(nome= nome_, tipo=tipo_, descricao= descricao_)
        db_session = local_session()
        try:
            db_session.add(dados_pessoa)
            db_session.commit()
            flash('Pessoa criada com sucesso!', 'success')
            return redirect(url_for('get_recursos'))
        except SQLAlchemyError as e:
            print(f'Erro ao cadastrar pessoa: {e}')
            flash(f'Erro no banco ao cadastrar pessoa: {e}', 'error')
            db_session.rollback()
            return render_template('criar_recurso.html')
        except Exception as ex:
            print(f'Erro a ser analisado: {ex}')
            flash(f'Erro ao cadastrar pessoa: {ex}', 'error')
            db_session.rollback()
            return render_template('criar_recurso.html')
        finally:
            db_session.close()
    return render_template('criar_recurso.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003, host="0.0.0.0") # Rodar em uma porta diferente da API principal