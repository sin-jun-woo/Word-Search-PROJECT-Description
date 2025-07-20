# --- 1. 라이브러리 및 모듈 가져오기 ---
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
# 직접 만든 유틸리티 및 모듈들
from auth_utils import hash_password, verify_password, create_access_token, verify_token
from schemas import UserCreate, UserLogin, UserResponse, Token, GameResponse, GameCreate, ResultResponse, ResultCreate, CommentCreate, CommentResponse
from models import User, Game, Base
from database import engine, get_db
from crud import (
    create_game as create_game_crud,
    get_games as get_games_crud,
    game_detail,
    delete_game as delete_game_crud,
    create_result as create_result_crud,
    results_detail,
    create_comment_crud, 
    get_comments_by_game, 
    delete_comment_crud
)
from fastapi.middleware.cors import CORSMiddleware

# --- 2. 애플리케이션 초기 설정 ---

# models.py에 정의된 모든 테이블을 데이터베이스에 생성합니다 (이미 존재하면 넘어감).
Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 인스턴스를 생성합니다.
app = FastAPI()

# Bearer 토큰 인증 스키마를 설정합니다.
oauth2_scheme = HTTPBearer()

# --- 3. 인증 및 의존성 주입 ---

# 요청 헤더의 토큰을 검증하고, 유효하면 해당 사용자 정보를 DB에서 가져오는 함수입니다.
# 이 함수는 다른 엔드포인트에서 '의존성(Dependency)'으로 주입되어,
# 인증이 필요한 API를 보호하는 역할을 합니다.
def get_current_user(credentials: HTTPBearer = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# --- 4. API 엔드포인트 (라우트) 정의 ---

# [인증] 회원가입
@app.post("/auth/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 이미 존재하는 이메일인지 확인합니다.
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 새 사용자 객체를 생성하고 비밀번호를 해싱하여 저장합니다.
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# [인증] 로그인
@app.post("/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    # 사용자가 존재하지 않거나 비밀번호가 틀리면 에러를 발생시킵니다.
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # JWT 액세스 토큰을 생성하여 반환합니다.
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type" : "bearer"}

# [인증] 내 정보 확인 (인증 필요)
@app.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    # get_current_user 의존성을 통해 인증된 사용자 정보를 바로 받아옵니다.
    return current_user

# [게임] 게임 생성 (인증 필요)
@app.post("/games", response_model=GameResponse)
def create_game(game_data: GameCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # crud.py의 함수를 호출하여 게임 생성 로직을 수행합니다.
    return create_game_crud(db, game_data, created_by=current_user.id)

# [게임] 게임 목록 조회
@app.get("/games", response_model=list[GameResponse])
def list_games(db: Session = Depends(get_db)):
    return get_games_crud(db)

# [게임] 게임 상세 조회
@app.get("/games/{game_id}", response_model=GameResponse)
def read_game(game_id: int, db: Session = Depends(get_db)):
    game = game_detail(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

# [게임] 게임 삭제 (인증 필요)
@app.delete("/games/{game_id}")
def delete_game_endpoint(game_id:int, db:Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 게임을 생성한 유저만 삭제할 수 있도록 권한을 확인합니다.
    if game.created_by != current_user.id :
        raise HTTPException(status_code=403, detail="Not authorized to delete this game")
    
    delete_game_crud(db, game_id)
    return {"message": "Game deleted successfully"}

# [결과] 게임 결과 저장 및 브로드캐스트
@app.post("/games/{game_id}/results", response_model=ResultResponse)
async def create_result_save(game_id: int, result_data: ResultCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 먼저 결과를 DB에 저장합니다.
    result = create_result_crud(db, game_id, result_data)
    
    # 오래 걸릴 수 있는 브로드캐스트 작업은 백그라운드에서 실행합니다.
    # 이렇게 하면 클라이언트는 즉시 응답을 받고, 서버는 뒤에서 조용히 작업을 처리합니다.
    background_tasks.add_task(
        broadcast_result, game_id, {
            "player_name": result.player_name,
            "time_token": result.time_token,
            "found_words": result.found_words,
            "create_at": str(result.create_at)
        })
    
    return result

# [결과] 게임 결과 목록 조회
@app.get("/games/{game_id}/results", response_model=list[ResultResponse])
def results_list(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return results_detail(db, game_id)

# --- 5. WebSocket 실시간 통신 설정 ---

# 각 게임 ID별로 연결된 WebSocket 클라이언트 목록을 저장하는 딕셔너리입니다.
game_connections: dict[int, list[WebSocket]] = {}

# WebSocket 연결을 처리하는 엔드포인트입니다.
@app.websocket("/ws/games/{game_id}/results")
async def websocket_game_results(websocket: WebSocket, game_id: int):
    await websocket.accept()
    
    # 해당 게임의 연결 목록에 현재 클라이언트를 추가합니다.
    if game_id not in game_connections:
        game_connections[game_id] = []
    game_connections[game_id].append(websocket)
    
    try:
        # 클라이언트 연결이 끊어질 때까지 계속 대기합니다.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # 연결이 끊어지면 목록에서 제거합니다.
        game_connections[game_id].remove(websocket)
        
# 특정 게임에 연결된 모든 클라이언트에게 메시지를 보내는 브로드캐스트 함수입니다.
async def broadcast_result(game_id: int, result_data: dict):
    if game_id in game_connections:
        for ws in game_connections[game_id]:
            await ws.send_json(result_data)
        print (f"game {game_id} 접속자에게 결과 전송됨")
        
# --- 6. 댓글 관련 엔드포인트 ---

# [댓글] 댓글 작성 (인증 필요)
@app.post("/games/{game_id}/comments", response_model=CommentResponse)
def create_comment(game_id: int, comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # ... (생략) ...
    comment = create_comment_crud(db, game_id, current_user.id, comment_data.content)
    return comment

# [댓글] 댓글 조회
@app.get("/games/{game_id}/comments", response_model=list[CommentResponse])
def list_comments(game_id: int, db: Session = Depends(get_db)):
    # ... (생략) ...
    return get_comments_by_game(db, game_id)

# [댓글] 댓글 삭제 (인증 필요)
@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = delete_comment_crud(db, comment_id, current_user.id)
    if result == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if result == "not_authorized":
        raise HTTPException(status_code=403, detail="Not authorized or comment not found")
    return {"message": "Comment deleted successfully"}

# --- 7. CORS 미들웨어 설정 ---

# 프론트엔드(예: http://localhost:5173)에서 오는 요청을 허용하기 위한 설정입니다.
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
