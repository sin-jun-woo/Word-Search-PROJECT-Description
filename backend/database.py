# 1. SQLAlchemy에서 필요한 함수들을 가져옵니다.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 2. 데이터베이스 연결 주소를 정의합니다.
# 여기서는 프로젝트 폴더에 'WordSearch.db'라는 이름의 SQLite 데이터베이스 파일을 사용하겠다는 의미입니다.
DATABASE_URL = "sqlite:///./WordSearch.db"

# 3. 데이터베이스 엔진을 생성합니다.
# 엔진은 SQLAlchemy가 데이터베이스와 통신하는 시작점입니다.
engine = create_engine(
    DATABASE_URL, 
    # SQLite는 기본적으로 한 번에 하나의 스레드만 접근을 허용합니다.
    # FastAPI는 비동기적으로 여러 스레드를 사용할 수 있으므로, 이 제한을 해제하는 옵션입니다.
    connect_args={"check_same_thread": False}
)

# 4. 데이터베이스 세션(Session)을 생성하는 클래스를 만듭니다.
# sessionmaker는 '세션 공장'과 같습니다. 이 공장을 통해 필요할 때마다 세션을 찍어낼 수 있습니다.
# autocommit=False: 데이터를 변경해도 자동으로 DB에 반영(commit)하지 않습니다.
# autoflush=False: 세션에 변경사항이 생겨도 자동으로 DB에 임시 저장(flush)하지 않습니다.
# bind=engine: 이 세션 공장이 위에서 만든 엔진을 사용하도록 연결합니다.
SeesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # 🚨 오타 제안: SeesionLocal -> SessionLocal

# 5. 선언적 모델링을 위한 기본 클래스(Base)를 생성합니다.
# models.py 파일의 모든 모델 클래스(User, Game 등)는 이 Base 클래스를 상속받아야 합니다.
# 이를 통해 SQLAlchemy가 파이썬 클래스와 데이터베이스 테이블을 매핑할 수 있습니다.
Base = declarative_base()

# 6. FastAPI 의존성 주입(Dependency Injection)을 위한 함수입니다.
# 이 함수는 API 엔드포인트가 호출될 때마다 실행되어 데이터베이스 세션을 제공하고,
# 요청 처리가 끝나면 세션을 안전하게 닫는 역할을 합니다.
def get_db():
    # 위에서 만든 '세션 공장'을 호출하여 새로운 데이터베이스 세션을 생성합니다.
    db = SeesionLocal()
    try:
        # yield 키워드를 사용하여 생성된 세션(db)을 API 엔드포인트에 전달합니다.
        # API 엔드포인트의 모든 작업이 이 시점에서 실행됩니다.
        yield db
    finally:
        # API 엔드포인트의 작업이 성공하든, 실패(에러 발생)하든 관계없이
        # finally 블록은 항상 실행되어 데이터베이스 세션을 닫아줍니다.
        # 이는 리소스 낭비를 막는 매우 중요한 패턴입니다.
        db.close()
