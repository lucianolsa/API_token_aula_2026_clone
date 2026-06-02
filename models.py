from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

# Base de dados
engine = create_engine('sqlite:///database.db')

db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class UsuarioExemplo(Base):
    __tablename__ = 'usuarios_exemplo'
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
            "papel":self.papel
        }
        return dados

class NotasExemplo(Base):
    __tablename__ = 'notas_exemplo'
    id = Column(Integer, primary_key=True)
    conteudo = Column(String, nullable=False)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    #user_id = Column(Integer, ForeignKey('usuarios_exemplo.id')) # Poderia ter para associar

Base.metadata.create_all(engine)  # Cria as tabelas