<script>
  // --- 1. 라이브러리 및 모듈 가져오기 ---
  import { push, link } from "svelte-spa-router"; // 페이지 이동(push) 및 링크(link) 기능을 위한 함수
  import { onMount } from "svelte"; // 컴포넌트가 처음 렌더링될 때 코드를 실행하기 위한 Svelte 생명주기 함수

  // --- 2. 컴포넌트 상태 변수 정의 ---
  let nickname = ""; // 사용자가 입력할 닉네임을 저장할 변수
  let games = []; // 서버에서 받아온 게임 목록을 저장할 배열
  let isLoading = true; // 게임 목록을 불러오는 중인지 여부를 나타내는 로딩 상태
  let error = null; // 데이터 로딩 중 오류 발생 시 메시지를 저장할 변수

  // --- 3. 컴포넌트 초기화 로직 (게임 목록 불러오기) ---
  // onMount는 컴포넌트가 화면에 처음 그려질 때 단 한 번 실행됩니다.
  onMount(async () => {
    try {
      // 백엔드 서버의 /games 엔드포인트로 GET 요청을 보내 게임 목록을 가져옵니다.
      const res = await fetch("http://127.0.0.1:8000/games");
      // 요청이 실패하면 (예: 서버 다운, 404 에러 등) 에러를 발생시킵니다.
      if (!res.ok) throw new Error("게임 목록을 불러오는 데 실패했습니다.");
      // 성공적으로 응답을 받으면, JSON 형식의 데이터를 파싱하여 games 배열에 저장합니다.
      games = await res.json();
    } catch (e) {
      // try 블록에서 에러가 발생하면, 그 메시지를 error 변수에 저장합니다.
      error = e.message;
    } finally {
      // 성공/실패 여부와 관계없이 로딩 상태를 종료합니다.
      isLoading = false;
    }
  });

  // --- 4. 게임 시작 함수 ---
  function startGame(gameId) {
    // 닉네임이 비어있는지 확인하고, 비어있으면 경고창을 띄우고 함수를 종료합니다.
    if (!nickname.trim()) return alert("닉네임을 입력해주세요!");
    // URL에 닉네임을 안전하게 포함시키기 위해 인코딩합니다. (예: '테스트 유저' -> '테스트%20유저')
    const encodedNickname = encodeURIComponent(nickname.trim());
    // svelte-spa-router의 push 함수를 사용해 게임 페이지로 이동합니다.
    // URL에 게임 ID와 닉네임을 포함하여 전달합니다.
    push(`/game/${gameId}?nickname=${encodedNickname}`);
  }

  // --- 5. 날짜 포맷팅 함수 ---
  function formatDate(dateStr) {
    // 서버에서 받은 날짜 문자열(ISO 형식)을 Date 객체로 변환합니다.
    const date = new Date(dateStr);
    // 사용자의 지역 설정에 맞는 날짜/시간 형식(예: 2023. 10. 27. 오후 3:14:00)으로 변환하여 반환합니다.
    return date.toLocaleString();
  }
</script>

<!-- 6. 화면에 표시될 HTML 구조 -->
<h1>🎮 Word Search Lobby</h1>
<p>게임에 참여할 닉네임을 입력해주세요</p>

<div class="nickname-input">
  <!-- input의 값을 nickname 변수와 양방향으로 바인딩합니다. -->
  <input bind:value={nickname} placeholder="닉네임 입력" />
</div>

<p>
  <!-- use:link는 svelte-spa-router의 기능으로, 클릭 시 페이지 새로고침 없이 /maker로 이동하게 해줍니다. -->
  <a href="/maker" use:link>게임 생성하기 (어드민)</a>
</p>

<hr />

<h2>게임 목록</h2>

<!-- 7. 조건부 렌더링 -->
{#if isLoading}
  <!-- 로딩 중일 때 표시될 내용 -->
  <p>게임 목록을 불러오는 중...</p>
{:else if error}
  <!-- 에러가 발생했을 때 표시될 내용 -->
  <p style="color: red;">{error}</p>
{:else if games.length === 0}
  <!-- 게임 목록이 비어있을 때 표시될 내용 -->
  <p>플레이할 수 있는 게임이 없습니다. 새 게임을 만들어보세요!</p>
{:else}
  <!-- 게임 목록이 성공적으로 로드되었을 때 표시될 내용 -->
  <div class="game-list">
    <!-- games 배열을 순회하며 각 게임 정보를 .game-card로 만듭니다. -->
    {#each games as game}
      <div class="game-card">
        <h3>{game.title}</h3>
        <p class="description">{game.description || "설명이 없습니다."}</p>
        <div class="meta">
          <span>제작자: {game.created_by || "알 수 없음"}</span>
          <!-- formatDate 함수를 사용해 날짜를 보기 좋게 표시합니다. -->
          <span>제작일: {formatDate(game.create_at)}</span>
        </div>
        <!-- 버튼 클릭 시 startGame 함수를 해당 게임의 id와 함께 호출합니다. -->
        <button on:click={() => startGame(game.id)}>플레이</button>
      </div>
    {/each}
  </div>
{/if}

<!-- 8. 컴포넌트 전용 스타일 -->
<style>
  .nickname-input {
    margin-bottom: 20px;
  }
  .nickname-input input {
    /* App.svelte에 정의된 CSS 변수를 사용해 다크/라이트 모드에 대응합니다. */
    background-color: var(--input-background);
    border: 1px solid var(--input-border);
    color: var(--text-color);
  }
  .game-list {
    display: grid;
    /* 화면 너비에 따라 카드 개수를 자동으로 조절하는 반응형 그리드 레이아웃 */
    /* 각 카드의 최소 너비는 300px이며, 공간이 남으면 1fr씩 차지합니다. */
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px; /* 카드 사이의 간격 */
  }
  .game-card {
    border: 1px solid var(--card-border);
    background-color: var(--card-background);
    padding: 15px;
    border-radius: 8px;
    display: flex;
    flex-direction: column; /* 카드 내부 요소들을 세로로 정렬 */
  }
  .game-card h3 {
    margin-top: 0;
  }
  .game-card .description {
    flex-grow: 1; /* 설명 부분이 남는 공간을 모두 차지하도록 하여 버튼을 아래에 고정 */
    color: var(--text-color-light);
    font-size: 0.9em;
  }
  .game-card .meta {
    font-size: 0.8em;
    color: var(--text-color-muted);
    margin-top: 10px;
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between; /* 제작자와 제작일을 양쪽 끝으로 정렬 */
  }
  button {
    width: 100%; /* 버튼이 카드 너비에 꽉 차도록 설정 */
  }
</style>
