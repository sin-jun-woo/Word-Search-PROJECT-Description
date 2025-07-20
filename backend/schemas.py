from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# --- 사용자 관련 스키마 ---

# 회원가입 시 요청 본문에 필요한 데이터 구조
class UserCreate(BaseModel):
    username: str   
    email: EmailStr  # Pydantic이 자동으로 이메일 형식인지 검사합니다.
    password: str

# 로그인 시 요청 본문에 필요한 데이터 구조
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
# API가 클라이언트에게 사용자 정보를 응답할 때의 데이터 구조
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    create_at: datetime # create_at 필드는 datetime 타입이어야 합니다.
    
    # Pydantic 설정 클래스
    class Config:
        # 이 설정을 통해 SQLAlchemy 같은 ORM 모델 객체를
        # Pydantic 모델로 자동으로 변환할 수 있습니다.
        # 예: db_user.id -> UserResponse.id
        from_attributes = True

# 다른 응답(예: 게임 정보) 안에 포함될 최소한의 사용자 정보 구조
class UserInResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

# --- 인증 관련 스키마 ---

# 로그인 성공 시 응답할 JWT 토큰의 구조
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" # 기본값을 "bearer"로 설정
    
# --- 게임 관련 스키마 ---

# 게임 생성 시 요청 본문에 필요한 데이터 구조
class GameCreate(BaseModel):
    title: str
    description: Optional[str] = None # description은 선택 사항이며, 없으면 None이 됩니다.
    word_list: List[str] # word_list는 문자열들의 리스트여야 합니다.
    
# API가 게임 정보를 응답할 때의 데이터 구조
class GameResponse(BaseModel):
    id :int
    title: str
    description: Optional[str] = None
    word_list: str # DB에는 JSON 문자열로 저장되므로 str 타입
    grid: str      # DB에는 JSON 문자열로 저장되므로 str 타입
    grid_size: int
    creator: UserInResponse # 게임 제작자 정보는 UserInResponse 스키마를 사용해 중첩됩니다.
    create_at: datetime
    
    class Config:
        from_attributes = True
        
# --- 게임 결과 관련 스키마 ---

# 게임 결과 저장 시 요청 본문에 필요한 데이터 구조
class ResultCreate(BaseModel):
    player_name: str
    time_token: int
    found_words : List[str]
    
# API가 게임 결과를 응답할 때의 데이터 구조
class ResultResponse(BaseModel):
    id: int
    game_id: int
    player_name: str
    time_token: int
    found_words: str # DB에는 JSON 문자열로 저장되므로 str 타입
    create_at: datetime
    
    # 🚨 오타 수정 제안: 'config'는 'Config'여야 합니다.
    class Config:
        from_attributes = True
    
# --- 댓글 관련 스키마 ---

# 댓글의 기본이 되는 스키마 (공통 필드 정의)
class CommentBase(BaseModel):
    content: str

# 댓글 생성 시 요청 본문에 필요한 데이터 구조
class CommentCreate(CommentBase):
    # CommentBase를 상속받아 content 필드를 그대로 사용합니다.
    pass
    
# API가 댓글 정보를 응답할 때의 데이터 구조
class CommentResponse(BaseModel):
    id: int
    content: str
    user: UserInResponse # 댓글 작성자 정보는 UserInResponse 스키마를 사용합니다.
    game_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
