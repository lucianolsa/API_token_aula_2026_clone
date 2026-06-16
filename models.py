from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

# Base de dados
#engine = create_engine('sqlite:///database.db',pool_size=10, max_overflow=20)

# Banco MySQL
engine = create_engine('mysql+pymysql://root:senaisp@localhost:3306/base_api')

db_session = scoped_session(sessionmaker(bind=engine))


Base = declarative_base()
Base.query = db_session.query_property()


class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, default='usuario')
    criado_em = Column(DateTime, nullable=False, server_default=func.now())


    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password_hash(self,senha):
        return check_password_hash(self.senha_hash,senha)

    def serialize(self):
        dados={
            "id":self.id,
            "nome":self.nome,
            "email":self.email,
            "papel":self.papel,
            "criado_em":self.criado_em.strftime("%d/%m/%Y %H:%M:%S")
        }
        return dados

class Atividade(Base):
    __tablename__ = 'atividades'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    pessoa_id = Column(Integer, ForeignKey('usuarios.id'))

class Recurso(Base):
    __tablename__ = 'recursos'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f'<Recurso={self.nome}, tipo={self.tipo}, descricao={self.descricao}>'

class AtividadeRecurso(Base):
    __tablename__ = 'atividades_recursos'
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividades.id'))
    recurso_id = Column(Integer, ForeignKey('recursos.id'))
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f'<AtividadeRecurso id={self.id}, atividade_id={self.atividade_id}, recurso_id={self.recurso_id}>'

Base.metadata.create_all(engine)  # Cria as tabelas