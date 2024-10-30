from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_subscription_active = Column(Boolean, default=False)
    
    # Добавляем связь с OAuthCredentials
    # uselist=False означает one-to-one отношение
    oauth_credentials = relationship(
        "OAuthCredentials", 
        back_populates="user",
        uselist=False
    )
