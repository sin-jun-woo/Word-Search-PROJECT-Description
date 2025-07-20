import json
import random
from enum import Enum # 제안: Enum 타입을 사용하기 위해 추가
from sqlalchemy.orm import Session, joinedload
from models import Game, Result, Comment, User
from schemas import GameCreate, ResultCreate

# 제안: 그리드 생성 실패 시 발생시킬 커스텀 예외 정의
class GridGenerationError(Exception):
    pass

# --- 단어 찾기 그리드 생성 ---
# 이 함수는 게임 보드를 만드는 핵심 알고리즘입니다.
def generate_word_search_grid(words: list[str], grid_size: int = 10):
    # 1. 지정된 크기의 빈 그리드를 초기화합니다.
    grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
    # 2. 일관성을 위해 모든 단어를 대문자로 변환합니다.
    words = [w.upper() for w in words]

    # 3. 단어가 배치될 수 있는 8가지 모든 방향(가로, 세로, 대각선)을 정의합니다.
    directions = [
        (0, 1), (1, 0), (1, 1), (1, -1),  # 오른쪽, 아래, 아래-오른쪽, 아래-왼쪽
        (0, -1), (-1, 0), (-1, -1), (-1, 1) # 왼쪽, 위, 위-왼쪽, 위-오른쪽
    ]

    # 4. 단어를 길이의 내림차순으로 정렬합니다. 이것은 더 길고 어려운 단어를 먼저 배치하여
    #    성공 확률을 높이는 영리한 휴리스틱(heuristic) 방법입니다.
    for word in sorted(words, key=len, reverse=True):
        placed = False
        # 5. 각 단어를 배치하기 위해 최대 200번 시도하여 유효한 위치를 찾습니다.
        for _ in range(200): 
            direction = random.choice(directions)
            dr, dc = direction # 행과 열의 변화량
            
            # 6. 무작위 시작 위치를 선택합니다.
            start_row = random.randint(0, grid_size - 1)
            start_col = random.randint(0, grid_size - 1)
            
            # 7. 단어가 그리드 경계 내에 맞는지 확인하기 위해 끝 위치를 계산합니다.
            end_row = start_row + (len(word) - 1) * dr
            end_col = start_col + (len(word) - 1) * dc

            if not (0 <= end_row < grid_size and 0 <= end_col < grid_size):
                continue # 단어가 경계를 벗어나면 다시 시도합니다.

            # 8. 선택된 경로가 비어 있거나 올바르게 겹치는지 확인합니다.
            can_place = True
            for i in range(len(word)):
                row, col = start_row + i * dr, start_col + i * dc
                # 셀에 이미 *다른* 글자가 있으면 경로는 유효하지 않습니다.
                if grid[row][col] != '' and grid[row][col] != word[i]:
                    can_place = False
                    break
            
            # 9. 경로가 유효하면 그리드에 단어를 배치합니다.
            if can_place:
                for i in range(len(word)):
                    row, col = start_row + i * dr, start_col + i * dc
                    grid[row][col] = word[i]
                placed = True
                break # 단어 배치를 성공했으므로 다음 단어로 넘어갑니다.
        
        if not placed:
            # 200번 시도 후에도 단어를 배치하지 못하면 경고를 발생시킵니다.
            raise GridGenerationError(f"'{word}' 단어를 배치할 수 없습니다. 단어 수를 줄이거나 더 짧은 단어를 사용해보세요.")

    # 10. 남은 빈 셀을 무작위 알파벳으로 채웁니다.
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    # 2차원 그리드를 데이터베이스에 저장하기 쉬운 1차원 리스트(flat_grid)로 만듭니다.
    flat_grid = [grid[r][c] or random.choice(alphabet) for r in range(grid_size) for c in range(grid_size)]
            
    # 11. 최종 그리드를 데이터베이스 저장을 위해 JSON 문자열로 직렬화합니다.
    return json.dumps(flat_grid)

# --- 게임 CRUD 작업 ---

def create_game(db: Session, game_data: GameCreate, created_by: int):
    grid_size = 10
    # 그리드 생성 함수를 호출하여 게임 보드를 만듭니다.
    try:
        grid_json = generate_word_search_grid(game_data.word_list, grid_size)
    except GridGenerationError as e:
        # 이 예외는 API 계층(main.py)에서 잡아 400 Bad Request 에러로 반환할 수 있습니다.
        raise e
        
    # 새로운 Game ORM 객체를 생성합니다.
    game = Game(
        title=game_data.title,
        description=game_data.description,
        # 단어 목록을 JSON 문자열로 저장합니다.
        word_list=json.dumps([w.upper() for w in game_data.word_list]),
        grid=grid_json,
        grid_size=grid_size,
        created_by=created_by
    )
    db.add(game)
    db.commit()
    db.refresh(game) # DB에서 새로 생성된 ID를 얻기 위해 객체를 새로고침합니다.
    return game

def get_games(db:Session):
    # joinedload(Game.creator)를 사용하여 연관된 User 객체를 단일 쿼리로 효율적으로
    # 가져와 N+1 쿼리 문제를 방지합니다.
    return db.query(Game).options(joinedload(Game.creator)).order_by(Game.create_at.desc()).all()

def game_detail(db:Session, game_id:int):
    # 단일 게임의 제작자 정보를 가져올 때도 joinedload를 사용합니다.
    return db.query(Game).options(joinedload(Game.creator)).filter(Game.id == game_id).first()

def delete_game(db:Session, game_id:int):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        db.delete(game)
        db.commit()
        return True
    return False

# --- 결과 CRUD 작업 ---

def create_result(db:Session, game_id:int, result_data:ResultCreate):
    # 찾은 단어 목록을 JSON 문자열로 직렬화합니다.
    # ensure_ascii=False는 한글 등 비-ASCII 문자를 올바르게 처리하기 위한 좋은 습관입니다.
    found_words_json = json.dumps(result_data.found_words, ensure_ascii=False)
    result = Result(
        game_id = game_id,
        player_name = result_data.player_name,
        time_token = result_data.time_token,
        found_words = found_words_json
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def results_detail(db:Session, game_id:int):
    return db.query(Result).filter(Result.game_id == game_id).all()

# --- 댓글 CRUD 작업 ---

class DeleteResult(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    NOT_AUTHORIZED = "not_authorized"

def create_comment_crud(db: Session, game_id: int, user_id: int, content: str):
    comment = Comment(
        content=content,
        user_id=user_id,
        game_id=game_id
        )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_comments_by_game(db: Session, game_id: int):
    # 댓글 작성자 정보를 효율적으로 가져오기 위해 joinedload를 사용합니다.
    return db.query(Comment).options(joinedload(Comment.user)).filter(Comment.game_id == game_id).order_by(Comment.created_at.desc()).all()

def delete_comment_crud(db: Session, comment_id: int, user_id: int) -> DeleteResult:
    # 댓글과 연관된 게임 정보를 한 번에 가져옵니다.
    comment = db.query(Comment).options(joinedload(Comment.game)).filter(Comment.id == comment_id).first()

    if not comment:
        return DeleteResult.NOT_FOUND

    # 권한 로직: 댓글 작성자이거나 게임 제작자인 경우에만 삭제를 허용합니다.
    is_author = comment.user_id == user_id
    is_game_creator = comment.game.created_by == user_id

    if not (is_author or is_game_creator):
        return DeleteResult.NOT_AUTHORIZED

    # 삭제 실행
    db.delete(comment)
    db.commit()
    return DeleteResult.SUCCESS
