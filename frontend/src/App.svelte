<script>
  // --- 1. 라이브러리 및 컴포넌트 가져오기 ---
  // svelte-spa-router는 URL 주소에 따라 다른 컴포넌트를 보여주는
  // 싱글 페이지 애플리케이션(SPA) 라우팅 기능을 제공합니다.
  import Router from "svelte-spa-router";

  // 각 페이지를 담당할 Svelte 컴포넌트들을 가져옵니다.
  import Maker from "./pages/Maker.svelte"; // 단어 찾기 게임 '생성' 페이지
  import Lobby from "./pages/Lobby.svelte"; // 게임 목록을 보여주는 '로비' 페이지
  import Game from "./pages/Game.svelte"; // 실제 '게임 플레이' 페이지

  // --- 2. 라우팅 규칙 정의 ---
  // 'URL 경로'와 '보여줄 컴포넌트'를 짝지어 정의하는 객체입니다.
  const routes = {
    // 웹사이트의 기본 주소('/')로 접속하면 Lobby 컴포넌트를 보여줍니다.
    "/": Lobby,

    // '/maker' 주소로 접속하면 Maker 컴포넌트를 보여줍니다.
    "/maker": Maker,

    // '/game/게임ID'와 같은 동적인 경로로 접속하면 Game 컴포넌트를 보여줍니다.
    // 여기서 ':id'는 '파라미터'로, Game 컴포넌트 내에서 실제 게임 ID 값으로 사용할 수 있습니다.
    "/game/:id": Game,
  };
</script>

<!-- 3. 화면에 표시될 HTML 구조 -->
<main>
  <!-- Router 컴포넌트를 화면에 렌더링합니다. -->
  <!-- 위에서 정의한 routes 객체를 {routes} 형태로 전달하면,
       Router가 현재 URL을 확인하고 그에 맞는 페이지 컴포넌트를 이 자리에 표시해줍니다. -->
  <Router {routes} />
</main>

<!-- 4. 앱 전체에 적용될 스타일 정의 -->
<style>
  /* :global(:root)는 CSS의 최상위 요소(<html>)에 변수를 선언하는 방법입니다. */
  /* 앱 전체에서 사용할 색상 변수들을 미리 정의합니다. (기본: 라이트 모드) */
  :global(:root) {
    --background-color: #ffffff; /* 전체 배경색 */
    --text-color: #213547; /* 기본 글자색 */
    --text-color-light: #555; /* 약간 밝은 글자색 */
    --text-color-muted: #777; /* 회색 계열 글자색 */
    --link-color: #4585d7; /* 링크 색상 */
    --card-background: #ffffff; /* 카드(게임 목록 등) 배경색 */
    --card-border: #e0e0e0; /* 카드 테두리 색 */
    --button-background: #f9f9f9; /* 버튼 배경색 */
    --button-hover-background: #e9e9e9; /* 버튼에 마우스 올렸을 때 배경색 */
    --input-background: #fff; /* 입력창 배경색 */
    --input-border: #ccc; /* 입력창 테두리 색 */
    --cell-background: #fff; /* 게임판 셀 배경색 */
    --cell-border: #ddd; /* 게임판 셀 테두리 색 */
    --game-over-background: #f0f8ff; /* 게임 종료창 배경색 */
    --game-over-border: #cce5ff; /* 게임 종료창 테두리 색 */
  }

  /* 사용자의 운영체제(OS)가 다크 모드로 설정되어 있을 경우 적용될 스타일입니다. */
  @media (prefers-color-scheme: dark) {
    :global(:root) {
      /* 위에서 정의한 변수들의 값을 다크 모드에 맞게 덮어씁니다. */
      --background-color: #121212;
      --text-color: rgba(255, 255, 255, 0.87);
      --text-color-light: rgba(255, 255, 255, 0.7);
      --text-color-muted: rgba(255, 255, 255, 0.5);
      --link-color: #8ab4f8;
      --card-background: #1e1e1e;
      --card-border: #444;
      --button-background: #333;
      --button-hover-background: #444;
      --input-background: #2a2a2a;
      --input-border: #555;
      --cell-background: #2a2a2a;
      --cell-border: #444;
      --game-over-background: #2a2a3a;
      --game-over-border: #444466;
    }
  }

  /* :global(태그)는 특정 컴포넌트에 종속되지 않고 앱 전체의 태그에 스타일을 적용합니다. */
  :global(body) {
    /* 위에서 정의한 변수를 var() 함수로 불러와 실제 색상을 적용합니다. */
    background-color: var(--background-color);
    color: var(--text-color);
    /* 색상 변경 시 0.2초 동안 부드럽게 전환되는 애니메이션 효과를 줍니다. */
    transition:
      background-color 0.2s,
      color 0.2s;
    /* 우리 앱이 라이트/다크 모드를 모두 지원함을 브라우저에 알려줍니다.
       이를 통해 브라우저 기본 UI(스크롤바 등)도 테마에 맞게 변경될 수 있습니다. */
    color-scheme: light dark;
  }

  /* 앱 전체의 <a> 태그에 일관된 스타일을 적용합니다. */
  :global(a) {
    color: var(--link-color);
  }

  /* 앱 전체의 <button> 태그에 일관된 스타일을 적용합니다. */
  :global(button) {
    background-color: var(--button-background);
    color: var(--text-color);
    border: 1px solid var(--card-border);
  }
  /* 버튼에 마우스를 올렸을 때의 스타일입니다. */
  :global(button:hover) {
    background-color: var(--button-hover-background);
  }
</style>
