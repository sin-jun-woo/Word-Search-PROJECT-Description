<script>
  // --- 1. 라이브러리 및 모듈 가져오기 ---
  import { push } from "svelte-spa-router"; // 페이지 이동(라우팅)을 위한 함수
  import { onMount } from "svelte"; // 컴포넌트가 처음 렌더링될 때 코드를 실행하기 위한 Svelte 생명주기 함수

  // --- 2. 컴포넌트 상태 변수 정의 ---
  let title = ""; // 게임 제목을 저장할 변수
  let description = ""; // 게임 설명을 저장할 변수
  let wordsText = ""; // 사용자가 입력한 단어 목록(콤마로 구분된 텍스트)
  let authToken = null; // 관리자 인증 후 서버에서 받은 토큰을 저장할 변수
  let isLoading = true; // 관리자 인증이 진행 중인지 여부를 나타내는 로딩 상태
  let authError = null; // 인증 과정에서 오류 발생 시 메시지를 저장할 변수

  // --- 3. 컴포넌트 초기화 로직 (관리자 자동 인증) ---
  // onMount는 컴포넌트가 화면에 처음 그려질 때 단 한 번 실행됩니다.
  onMount(async () => {
    // 관리자 계정 정보를 하드코딩합니다.
    const adminEmail = "admin@example.com";
    const adminPassword = "adminpassword";

    try {
      // 1단계: 관리자 계정으로 로그인 시도
      let res = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: adminEmail, password: adminPassword }),
      });

      // 2단계: 로그인 실패 시 (상태 코드 400은 보통 '잘못된 요청'을 의미하며, 여기서는 계정이 없는 경우로 간주)
      if (res.status === 400) {
        console.log("관리자 계정이 없어 새로 생성합니다.");
        // 2-1: 관리자 계정으로 회원가입 요청
        await fetch("http://127.0.0.1:8000/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: "admin",
            email: adminEmail,
            password: adminPassword,
          }),
        });

        // 2-2: 회원가입 후, 다시 로그인 시도
        res = await fetch("http://127.0.0.1:8000/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: adminEmail, password: adminPassword }),
        });
      }

      // 3단계: 최종 로그인 성공 여부 확인
      if (res.ok) {
        const data = await res.json();
        authToken = data.access_token; // 응답받은 액세스 토큰을 변수에 저장
        console.log("✅ 관리자 인증 성공");
      } else {
        // 최종적으로 로그인에 실패한 경우
        throw new Error(
          "관리자 인증에 실패했습니다. 백엔드 서버를 확인해주세요."
        );
      }
    } catch (e) {
      // 네트워크 오류 등 예외 발생 시
      authError = e.message;
      console.error("❌ 관리자 인증 과정에서 오류 발생", e);
    } finally {
      // 성공/실패 여부와 관계없이 로딩 상태를 종료
      isLoading = false;
    }
  });

  // --- 4. 게임 생성 함수 ---
  async function createGame() {
    // 인증 토큰이 없으면 게임 생성을 막음
    if (!authToken) {
      alert(
        "아직 관리자 인증이 완료되지 않았습니다. 잠시 후 다시 시도해주세요."
      );
      return;
    }

    // 입력된 단어 텍스트를 콤마(,) 기준으로 잘라 배열로 만듭니다.
    // trim()으로 각 단어의 앞뒤 공백을 제거하고, filter(Boolean)으로 빈 항목을 제거합니다.
    const wordArray = wordsText
      .split(",")
      .map((w) => w.trim())
      .filter(Boolean);

    // 서버 API에 보낼 데이터(payload)를 구성합니다.
    const payload = {
      title,
      description,
      word_list: wordArray,
    };

    // 서버에 게임 생성을 요청합니다. (POST /games)
    const res = await fetch("http://127.0.0.1:8000/games", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // 'Authorization' 헤더에 Bearer 토큰을 담아 보내, 이 요청이 인증된 사용자의 요청임을 증명합니다.
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(payload),
    });

    // 요청이 실패한 경우
    if (!res.ok) {
      console.error("❌ 게임 생성 실패", res.status, await res.text());
      alert(`게임 생성에 실패했습니다. (에러: ${res.status})`);
      return;
    }

    // 요청이 성공한 경우
    const data = await res.json();
    console.log("✅ 게임 생성 성공:", data);

    // 생성된 게임 페이지로 사용자를 이동시킵니다.
    // 닉네임은 'Admin'으로 고정하여 URL 쿼리 파라미터로 전달합니다.
    push(`/game/${data.id}?nickname=Admin`);
  }
</script>

<!-- 5. 화면에 표시될 HTML 구조 -->
<h1>🛠 Word Search Maker</h1>

{#if isLoading}
  <!-- 관리자 인증 중일 때 표시될 내용 -->
  <p>관리자 인증 중...</p>
{:else if authError}
  <!-- 인증 오류가 발생했을 때 표시될 내용 -->
  <p style="color: red;">{authError}</p>
{:else}
  <!-- 인증이 성공적으로 완료되었을 때 표시될 게임 생성 폼 -->
  <div class="form-container">
    <label for="title-input">게임 제목</label>
    <input id="title-input" bind:value={title} placeholder="게임 제목" />

    <label for="desc-input">게임 설명</label>
    <input id="desc-input" bind:value={description} placeholder="게임 설명" />

    <label for="words-input">단어 리스트 (콤마로 구분)</label>
    <input
      id="words-input"
      bind:value={wordsText}
      placeholder="APPLE, BANANA, ORANGE"
    />

    <!-- on:click으로 createGame 함수를 연결합니다. -->
    <!-- disabled 속성을 사용해 제목이나 단어가 입력되지 않으면 버튼을 비활성화합니다. -->
    <button on:click={createGame} disabled={!title || !wordsText}>
      게임 생성
    </button>
  </div>
{/if}

<!-- 6. 컴포넌트 전용 스타일 -->
<style>
  .form-container {
    display: flex;
    flex-direction: column; /* 자식 요소들을 세로로 정렬 */
    gap: 10px; /* 요소들 사이의 간격 */
    max-width: 400px; /* 최대 너비 제한 */
    margin: auto; /* 가운데 정렬 */
  }
  input {
    padding: 8px;
    font-size: 1em;
  }
  /* 버튼이 비활성화(disabled) 상태일 때의 스타일 */
  button:disabled {
    background-color: #ccc;
    cursor: not-allowed; /* 마우스 커서를 '금지' 모양으로 변경 */
  }
</style>
