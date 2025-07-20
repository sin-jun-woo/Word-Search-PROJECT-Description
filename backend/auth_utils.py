from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

# --- 설정 변수 ---
# 🚨 [보안 취약점] SECRET_KEY는 절대 코드에 하드코딩하면 안 됩니다.
# 이 키가 노출되면 누구나 유효한 토큰을 만들어 시스템에 접근할 수 있습니다.
# 환경 변수나 별도의 설정 파일을 통해 관리해야 합니다.
SECRET_KEY = "secret"
ALGORITHM = "HS256" # 토큰 서명에 사용할 해시 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 액세스 토큰의 유효 기간 (60분)

# --- 비밀번호 처리 설정 ---
# passlib 라이브러리를 사용하여 비밀번호 해싱 및 검증을 처리합니다.
# 'bcrypt'는 현재 가장 널리 쓰이는 안전한 해싱 알고리즘 중 하나입니다.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 함수 정의 ---

# 1. 비밀번호 해시 함수
def hash_password(password: str) -> str:
    """
    평문 비밀번호를 받아 bcrypt 해시 값으로 변환합니다.
    동일한 비밀번호라도 매번 다른 해시 값이 생성됩니다. (솔트 자동 적용)
    """
    return pwd_context.hash(password)

# 2. 비밀번호 검증 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    사용자가 입력한 평문 비밀번호와 DB에 저장된 해시된 비밀번호를 비교하여
    일치하는지 여부를 True/False로 반환합니다.
    """
    return pwd_context.verify(plain_password, hashed_password)

# 3. 액세스 토큰 생성 함수
def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """
    사용자 정보(data)를 받아 JWT 액세스 토큰을 생성합니다.
    """
    to_encode = data.copy()
    # 토큰 만료 시간을 계산합니다. (현재 UTC 시간 + 유효 기간)
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    # 토큰에 만료 시간 정보('exp' 클레임)를 추가합니다.
    to_encode.update({"exp": expire})
    # 최종적으로 SECRET_KEY를 사용하여 토큰을 서명하고 인코딩합니다.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 4. 토큰 검증 함수
def verify_token(token: str):
    """
    클라이언트로부터 받은 토큰을 검증하고, 유효하면 그 내용을(payload) 반환합니다.
    """
    try:
        # SECRET_KEY를 사용하여 토큰을 디코딩하고 서명을 검증합니다.
        # 만약 토큰이 변조되었거나, 만료되었거나, 키가 다르면 JWTError가 발생합니다.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # 토큰이 유효하지 않은 경우 None을 반환합니다.
        return None
