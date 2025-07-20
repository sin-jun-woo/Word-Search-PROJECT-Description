<script>
  // --- 1. 라이브러리 및 Props 가져오기 ---
  // 'params'는 svelte-spa-router가 URL 파라미터(예: 게임 ID)를 담아 자동으로 전달하는 prop입니다.
  export let params;
  // Svelte의 생명주기 함수: onMount는 컴포넌트가 DOM에 추가된 후, onDestroy는 제거되기 전에 실행됩니다.
  import { onMount, onDestroy } from "svelte";
  // svelte-spa-router 헬퍼: querystring은 URL의 쿼리 문자열을 담는 읽기용 스토어, push는 페이지 이동 함수입니다.
  import { querystring, push } from "svelte-spa-router";

  // --- 2. 핵심 상태 변수 ---
  let gameData = null; // 서버에서 가져온 게임의 모든 정적 데이터(그리드, 단어 등)를 저장합니다.
  let timer = 0; // 게임 타이머 (초 단위)
  let interval = null; // 나중에 타이머를 중지시키기 위해 setInterval의 참조를 저장합니다.
  let ws = null; // 실시간 통신을 위한 WebSocket 객체입니다.
  let allSubmissions = []; // 이 게임에 대한 모든 플레이어의 결과 제출 기록을 담는 배열입니다.
  let isGameFinished = false; // 현재 플레이어가 게임을 완료했는지 추적하는 플래그입니다.

  // --- 3. 반응형 상태 (Svelte의 마법) ---
  // Svelte의 '$:' 문법은 반응형 구문을 만듭니다. 의존하는 변수가 바뀔 때마다 코드가 다시 실행됩니다.

  // $: URL의 쿼리 문자열에서 'nickname'을 추출합니다 (예: ?nickname=Player1).
  // URL이 변경되면 자동으로 업데이트됩니다.
  $: urlParams = new URLSearchParams($querystring);
  $: nickname = urlParams.get("nickname") || "익명 플레이어";

  // $: 이 변수들은 gameData로부터 '파생'됩니다. gameData가 서버에서 로드되면,
  // 이 변수들은 자동으로 계산되고 채워집니다.
  $: gridLetters = gameData ? JSON.parse(gameData.grid) : [];
  $: gridSize = gameData ? gameData.grid_size : 10;
  $: wordList = gameData ? JSON.parse(gameData.word_list) : [];
  $: maxWordLen = gameData ? Math.max(...wordList.map((w) => w.length)) : 0;

  // $: 그리드 셀의 시각적 상태를 관리합니다.
  $: selectedCells = Array(gridSize * gridSize).fill(false);
  // 'foundWords'는 고유한 단어를 효율적으로 추가하고 확인하기 위해 Set을 사용합니다.
  let foundWords = new Set();

  // $: 가장 강력한 반응형 블록입니다. 전체 리더보드는
  // 'allSubmissions'나 'wordList'가 변경될 때마다 자동으로 다시 계산됩니다.
  $: leaderboard = (() => {
    const totalWords = wordList.length;
    // 각 플레이어의 *최고* 점수만 효율적으로 저장하기 위해 Map을 사용합니다.
    const playerBestScores = new Map();

    for (const submission of allSubmissions) {
      try {
        const playerName = submission.player_name;
        // 서버는 found_words를 JSON 문자열로 보내므로, 파싱해야 합니다.
        const words = JSON.parse(submission.found_words);
        const score = words.length;
        const time = submission.time_token;
        const finished = totalWords > 0 && score === totalWords;

        const currentBest = playerBestScores.get(playerName);

        // 플레이어의 최고 점수를 업데이트하는 조건:
        // 1. 이전 기록이 없거나,
        // 2. 새 점수가 더 높거나,
        // 3. 점수는 같지만 시간이 더 빠를 경우.
        if (
          !currentBest ||
          score > currentBest.score ||
          (score === currentBest.score && time < currentBest.time)
        ) {
          playerBestScores.set(playerName, {
            name: playerName,
            score,
            time,
            finished,
          });
        }
      } catch (e) {
        console.error("결과를 처리하는 중 오류 발생:", submission, e);
      }
    }

    // 최고 점수 Map을 배열로 변환하고 정렬합니다.
    // 1차 정렬: 점수 (내림차순), 2차 정렬: 시간 (오름차순).
    return Array.from(playerBestScores.values()).sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.time - b.time;
    });
  })();

  // --- 4. 생명주기 함수 ---
  onMount(async () => {
    // 메인 게임 데이터를 가져옵니다.
    const res = await fetch(`http://127.0.0.1:8000/games/${params.id}`);
    if (res.ok) gameData = await res.json();

    // 초기 리더보드를 채우기 위해 이 게임의 모든 기존 결과를 가져옵니다.
    const resultsRes = await fetch(
      `http://127.0.0.1:8000/games/${params.id}/results`
    );
    if (resultsRes.ok) allSubmissions = await resultsRes.json();

    // 게임 타이머를 시작합니다.
    interval = setInterval(() => {
      if (!isGameFinished) timer++;
    }, 1000);

    // 실시간 업데이트를 위해 WebSocket 연결을 설정합니다.
    ws = new WebSocket(`ws://127.0.0.1:8000/ws/games/${params.id}/results`);
    ws.onopen = () => console.log("✅ WebSocket 연결 성공");
    ws.onmessage = (event) => {
      console.log("📥 WebSocket 메시지 수신:", event.data);
      try {
        const newSubmission = JSON.parse(event.data);
        // 새 결과가 도착했습니다! 'allSubmissions'에 추가합니다.
        // Svelte의 반응성 덕분에 'leaderboard' 계산이 자동으로 실행됩니다.
        allSubmissions = [...allSubmissions, newSubmission];
      } catch (e) {
        console.error("WebSocket 메시지 파싱 오류:", e);
      }
    };
    ws.onclose = () => console.log("🔌 WebSocket 연결 종료");
    ws.onerror = (error) => console.error("❌ WebSocket 오류:", error);
  });

  // onDestroy는 메모리 누수를 방지하는 데 매우 중요합니다.
  onDestroy(() => {
    if (interval) clearInterval(interval); // 타이머를 멈춥니다.
    if (ws) ws.close(); // WebSocket 연결을 닫습니다.
  });

  // --- 5. 게임 로직 및 이벤트 핸들러 ---
  let selectedPath = []; // 사용자가 순서대로 클릭한 셀 인덱스의 배열입니다.

  function handleCellClick(index) {
    if (isGameFinished || selectedCells[index] === "found") return;

    // 선택 토글: 셀이 이미 경로에 있으면 제거하고, 없으면 추가합니다.
    selectedPath = selectedPath.includes(index)
      ? selectedPath.filter((i) => i !== index)
      : [...selectedPath, index];

    const selectedWord = selectedPath.map((i) => gridLetters[i]).join("");

    // 선택한 단어가 정답인지 확인합니다.
    if (wordList.includes(selectedWord)) {
      alert(`✅ ${selectedWord} 찾았다!`);
      foundWords.add(selectedWord);
      foundWords = foundWords; // Set의 변경을 Svelte에 알리기 위해 재할당합니다.

      sendResultToServer(); // 서버에 알립니다 (WebSocket을 통해 다른 플레이어에게도).

      selectedPath.forEach((i) => (selectedCells[i] = "found"));
      selectedPath = []; // 경로를 초기화합니다.

      checkGameComplete();
    } else if (maxWordLen > 0 && selectedWord.length >= maxWordLen) {
      // 단어가 틀렸고 가능한 최대 길이에 도달했다면 초기화합니다.
      alert("❌ 틀렸습니다!");
      resetSelection();
    }

    // 즉각적인 피드백을 위해 셀의 시각적 상태를 업데이트합니다.
    selectedCells = selectedCells.map((v, i) =>
      selectedPath.includes(i) ? "selected" : v === "found" ? "found" : false
    );
  }

  function resetSelection() {
    selectedPath = [];
    selectedCells = selectedCells.map((v) => (v === "found" ? "found" : false));
  }

  function checkGameComplete() {
    if (wordList.length > 0 && foundWords.size === wordList.length) {
      isGameFinished = true; // 게임 완료 플래그를 설정합니다.
      // 타이머는 setInterval 콜백 내부에서 멈춥니다.
      setTimeout(() => {
        alert(`🎉 게임 클리어! 최종 기록: ${timer}초`);
      }, 100);
    }
  }

  async function sendResultToServer() {
    const payload = {
      player_name: nickname,
      time_token: timer,
      found_words: Array.from(foundWords), // JSON으로 보내기 위해 Set을 배열로 변환합니다.
    };
    try {
      await fetch(`http://127.0.0.1:8000/games/${params.id}/results`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error("결과 전송 중 네트워크 오류:", error);
    }
  }

  // --- 6. UI 헬퍼 함수 ---
  function goToHome() {
    push("/");
  }

  async function copyGameLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("게임 링크가 클립보드에 복사되었습니다!");
    } catch (err) {
      console.error("링크 복사 실패:", err);
    }
  }
</script>

<!-- 7. HTML 템플릿 -->
{#if gameData}
  <!-- 메인 게임 UI는 gameData를 가져온 후에만 렌더링됩니다. -->
  <div class="header">
    <h1>🎮 {gameData.title}</h1>
    <p>{gameData.description}</p>
    <p>
      <!-- 타이머 표시, MM:SS 형식으로 포맷팅 -->
      ⏳ {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, "0")}
    </p>
  </div>

  <div class="game-container">
    <!-- 왼쪽 패널: 단어 목록 -->
    <div class="game-left">
      <h3>📜 찾아야 할 단어</h3>
      <ul>
        {#each wordList as word}
          <!-- 단어를 찾았으면 'done' 클래스를 동적으로 적용합니다. -->
          <li class:done={foundWords.has(word)}>
            {foundWords.has(word) ? "✅" : "⬜️"}
            {word}
          </li>
        {/each}
      </ul>
    </div>

    <!-- 중앙 패널: 게임 그리드 -->
    <!-- CSS 변수 '--grid-size'를 통해 게임 데이터에 기반한 동적 그리드 레이아웃을 구현합니다. -->
    <div class="game-center" style="--grid-size: {gridSize}">
      {#each gridLetters as letter, i}
        <div
          role="button"
          tabindex="0"
          class="cell
            {selectedCells[i] === 'found' ? 'found' : ''} 
            {selectedCells[i] === 'selected' ? 'selected' : ''}"
          on:click={() => handleCellClick(i)}
          on:keydown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleCellClick(i);
            }
          }}
        >
          {letter}
        </div>
      {/each}
    </div>

    <!-- 오른쪽 패널: 리더보드 -->
    <div class="game-right">
      <h3>🏆 현황판</h3>
      <p class="my-score">
        <strong>내 점수:</strong>
        {foundWords.size} / {wordList.length}개
      </p>
      <hr />
      <ol class="leaderboard">
        <!-- 'leaderboard' 배열은 반응형이며, 변경 시 이 목록을 다시 렌더링합니다. -->
        {#each leaderboard as player, i}
          <li class:top-rank={i < 3}>
            <span class="rank">
              {#if i === 0}🥇{:else if i === 1}🥈{:else if i === 2}🥉{:else}{i +
                  1}.{/if}
            </span>
            <span class="name">{player.name}</span>
            <span class="score">
              {#if player.finished}
                <!-- 게임을 완료한 플레이어는 최종 시간을 표시합니다. -->
                <span class="final-time">🏁 {player.time}초</span>
              {:else}
                <!-- 진행 중인 플레이어는 현재 점수를 표시합니다. -->
                {player.score}점
              {/if}
            </span>
          </li>
        {/each}
      </ol>
    </div>
  </div>

  <!-- 게임 오버 UI: 현재 플레이어가 완료했을 때만 표시됩니다. -->
  {#if isGameFinished}
    <div class="game-over-controls">
      <h3>게임 종료!</h3>
      <p>
        수고하셨습니다! 다른 게임을 플레이하거나, 이 게임을 친구에게
        공유해보세요.
      </p>
      <div class="buttons">
        <button on:click={goToHome}>🏠 홈으로 나가기</button>
        <button on:click={copyGameLink}>🔗 게임 링크 복사</button>
      </div>
    </div>
  {/if}
{:else}
  <!-- gameData를 사용할 수 있기 전에 표시되는 로딩 메시지 -->
  <p>⏳ 게임 데이터를 불러오는 중...</p>
{/if}

<!-- 8. 컴포넌트 전용 스타일 -->
<style>
  .game-container {
    display: grid;
    /* 반응형 3열 레이아웃 */
    grid-template-columns: 200px 1fr 200px;
    gap: 20px;
    padding: 20px;
  }

  .game-left,
  .game-right {
    /* 일관된 테마를 위해 App.svelte에 정의된 CSS 변수를 사용합니다. */
    background: var(--card-background);
    padding: 10px;
    border-radius: 10px;
    border: 1px solid var(--card-border);
  }

  .game-left li.done {
    text-decoration: line-through;
    color: green;
    font-weight: bold;
  }

  .game-center {
    display: grid;
    /* 그리드 열은 템플릿의 '--grid-size' 변수에 의해 동적으로 설정됩니다. */
    grid-template-columns: repeat(var(--grid-size, 10), 40px);
    gap: 5px;
    justify-content: center;
  }

  .cell {
    width: 40px;
    height: 40px;
    background: var(--cell-background);
    border: 1px solid var(--cell-border);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: bold;
    transition: background 0.2s;
    user-select: none; /* 빠르게 클릭할 때 텍스트가 선택되는 것을 방지합니다. */
  }

  .cell.found {
    background: lightgreen;
    pointer-events: none; /* 찾은 셀은 클릭할 수 없게 만듭니다. */
  }
  .cell.selected {
    background: yellow;
  }

  /* ... 헤더, 리더보드 등을 위한 기타 스타일 ... */
  .header {
    text-align: center;
    margin-bottom: 20px;
  }

  .my-score {
    margin-bottom: 15px;
    font-size: 1.1em;
  }

  .leaderboard {
    list-style: none;
    padding: 0;
  }

  .leaderboard li {
    display: flex;
    align-items: center;
    padding: 8px 4px;
    border-bottom: 1px solid var(--card-border);
    transition: background-color 0.2s;
  }

  .leaderboard li.top-rank {
    font-weight: bold;
  }

  .leaderboard .rank {
    width: 40px;
    text-align: center;
    font-size: 1.2em;
  }
  .leaderboard .name {
    flex-grow: 1;
  }
  .leaderboard .score {
    font-family: monospace;
  }

  .final-time {
    color: #2e8b57; /* SeaGreen */
    font-weight: bold;
  }

  .game-over-controls {
    margin-top: 30px;
    padding: 20px;
    text-align: center;
    background-color: var(--game-over-background);
    border-radius: 8px;
    border: 1px solid var(--game-over-border);
  }

  .game-over-controls h3 {
    margin-top: 0;
  }

  .game-over-controls .buttons {
    margin-top: 15px;
  }

  .game-over-controls button {
    margin: 0 10px;
  }
</style>
