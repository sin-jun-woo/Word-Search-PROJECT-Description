from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base # database.py에서 정의한 선언적 기반 클래스
from datetime import datetime

# --- 유저 모델 ---
# 'Users' 테이블을 정의하는 클래스
class User(Base):
    __tablename__ = "Users" # 데이터베이스에 생성될 테이블의 이름
    
    # 컬럼 정의
    id = Column(Integer, primary_key=True, index=True) # 고유 ID, 기본 키
    username = Column(String, nullable=False) # 사용자 이름, 비어있을 수 없음
    email = Column(String, unique=True, nullable=False) # 이메일, 고유해야 하며 비어있을 수 없음
    password_hash = Column(String, nullable=False) # 해시된 비밀번호, 비어있을 수 없음
    create_at = Column(DateTime, default=datetime.utcnow) # 계정 생성 시간, 기본값으로 현재 UTC 시간이 저장됨
    
    # 관계(Relationship) 정의
    # 'Game' 모델과 'creator' 필드를 통해 일대다(One-to-Many) 관계를 맺음
    games = relationship("Game", back_populates="creator")
    # 'Comment' 모델과 'user' 필드를 통해 일대다 관계를 맺음
    # cascade="all, delete-orphan": 사용자가 삭제되면, 해당 사용자가 작성한 모든 댓글도 함께 삭제됨
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    
# --- 게임 모델 ---
# 'Games' 테이블을 정의하는 클래스
class Game(Base):
    __tablename__ = "Games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) # 게임 제목
    description = Column(Text) # 게임 설명
    word_list = Column(Text) # 단어 목록 (JSON 문자열로 저장)
    grid = Column(Text) # 단어 찾기 판 (JSON 문자열로 저장)
    grid_size = Column(Integer) # 단어 찾기 판의 크기
    created_by = Column(Integer, ForeignKey("Users.id")) # 외래 키, 'Users' 테이블의 'id'를 참조
    create_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    # 'User' 모델과 'games' 필드를 통해 다대일(Many-to-One) 관계를 맺음
    creator = relationship("User", back_populates="games")
    # 'Result' 모델과 'game' 필드를 통해 일대다 관계를 맺음
    results = relationship("Result", back_populates="game")
    # 'Comment' 모델과 'game' 필드를 통해 일대다 관계를 맺음
    # 게임이 삭제되면, 해당 게임에 달린 모든 댓글도 함께 삭제됨
    comments = relationship("Comment", back_populates="game", cascade="all, delete-orphan")
    
# --- 결과 모델 ---
# 'Results' 테이블을 정의하는 클래스
class Result(Base):
    __tablename__ = "Results"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("Games.id")) # 외래 키, 'Games' 테이블의 'id'를 참조
    player_name = Column(String, nullable=False) # 플레이어 이름
    time_token = Column(Integer) # 게임 클리어에 걸린 시간 (초)
    found_words = Column(String) # 찾은 단어 목록 (JSON 문자열로 저장)
    create_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 정의
    # 'Game' 모델과 'results' 필드를 통해 다대일 관계를 맺음
    game = relationship("Game", back_populates="results")

# --- 댓글 모델 ---
# 'Comments' 테이블을 정의하는 클래스
class Comment(Base):
    __tablename__ = "Comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False) # 댓글 내용
    created_at = Column(DateTime, default=datetime.utcnow) # 🚨 다른 모델과 필드명이 다름 ('create_at')

    # 외래 키 정의
    # ondelete="CASCADE": 참조하는 User 또는 Game이 삭제될 때 이 댓글도 데이터베이스 레벨에서 함께 삭제됨
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("Games.id", ondelete="CASCADE"), nullable=False)

    # 관계 정의
    user = relationship("User", back_populates="comments")
    game = relationship("Game", back_populates="comments")
