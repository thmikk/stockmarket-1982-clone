const socket = io();
let username = null;
let currentMode = "intro";
let currentShare = "";
let isHost = false;
let selectedDifficulty = 1;
let selectedGoal = 1000000;
let activityLog = [];

const screen = document.getElementById("screen");
const gameContent = document.getElementById("game-content");
const activityPanel = document.getElementById("activity-panel");
const activityLogDiv = document.getElementById("activity-log");
const input = document.getElementById("input");

function clearScreen() {
  gameContent.innerHTML = "";
}

function setScreenContent(content) {
  gameContent.innerHTML = `<pre>${content}</pre>`;
}

function switchToTwoColumnLayout() {
  screen.classList.remove("single-column");
  screen.classList.add("game-column");
  activityPanel.style.display = "block";
  updateActivityLog();
}

function switchToSingleColumnLayout() {
  screen.classList.add("single-column");
  screen.classList.remove("game-column");
  activityPanel.style.display = "none";
}

function addActivityEntry(type, message, playerName = null) {
  const timestamp = new Date().toLocaleTimeString();
  const entry = {
    type: type,
    message: message,
    playerName: playerName,
    timestamp: timestamp
  };
  
  activityLog.push(entry);
  
  // Keep only last 30 entries for better readability
  if (activityLog.length > 30) {
    activityLog.shift();
  }
  
  // Always update the log immediately
  updateActivityLog();
}

function updateActivityLog() {
  if (!activityLogDiv) return;
  
  let content = "";
  activityLog.forEach(entry => {
    const isCurrentPlayer = entry.playerName === username;
    const cssClass = `activity-entry ${entry.type}${isCurrentPlayer ? ' current-player' : ''}`;
    
    // Format each entry as a block element (div) to ensure line-by-line display
    content += `<div class="${cssClass}">`;
    content += `<span class="timestamp">[${entry.timestamp}]</span> `;
    
    if (entry.playerName) {
      content += `<span class="player-name">${entry.playerName}:</span> `;
    }
    
    content += `<span class="message">${entry.message}</span>`;
    content += `</div>`;
  });
  
  activityLogDiv.innerHTML = content;
  
  // Scroll to bottom to show latest entries
  activityLogDiv.scrollTop = activityLogDiv.scrollHeight;
}

function print(text = "") {
  const line = document.createElement("div");
  line.textContent = text;
  line.classList.add("screen-line");
  screen.appendChild(line);
}

function printHeader() {
  return "                 COMMODORE 64\n" +
         "                 64K RAM SYSTEM\n" +
         "                 READY.\n\n" +
         "****************************************\n" +
         "*           STOCKMARKET 1982           *\n" +
         "*              C64 EDITION             *\n" +
         "****************************************\n\n";
}

function showIntro() {
  switchToSingleColumnLayout();
  let content = printHeader();
  content += "Welcome to the original C64 Stock Market game!\n\n";
  content += "In this game you buy and sell shares in four\n";
  content += "different companies: LEAD, ZINC, TIN, and GOLD.\n\n";
  content += "Your goal is to become rich by buying low and\n";
  content += "selling high, while watching the market news\n";
  content += "for events that affect share prices.\n\n";
  content += "Press any key to start...";
  setScreenContent(content);
  currentMode = "intro";
}

function askForName() {
  switchToSingleColumnLayout();
  let content = printHeader();
  content += "Enter your name:";
  setScreenContent(content);
  currentMode = "ask-name";
}

function showLobby(players) {
  switchToSingleColumnLayout();
  let content = printHeader();
  content += "Waiting for players to join...\n\n";
  content += "Connected players:\n";
  players.forEach(p => content += "- " + p + "\n");
  
  if (isHost) {
    content += `\nCurrent settings: Difficulty=${selectedDifficulty}, Goal=$${selectedGoal}\n`;
    content += "Set difficulty (1-4) and goal (e.g. 1000000 or 5000000):\n";
    content += "Type: DIFF [1-4] or GOAL [amount] or START";
    currentMode = "host-lobby";
  } else {
    content += "\nWaiting for the host to start the game...";
    currentMode = "waiting";
  }
  
  setScreenContent(content);
}

input.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  const cmd = input.value.trim().toUpperCase();
  input.value = "";

  if (currentMode === "intro") {
    askForName();
    return;
  }

  if (currentMode === "ask-name") {
    if (cmd.length > 15) {
      let content = printHeader();
      content += "Enter your name:\n";
      content += "Name too long. Max 15 characters:";
      setScreenContent(content);
      return;
    }
    username = cmd;
    socket.emit("join", { username });
    let content = printHeader();
    content += `Welcome, ${username}!\n`;
    content += "Connecting to market...";
    setScreenContent(content);
    currentMode = "waiting";
    return;
  }

  if (currentMode === "host-lobby") {
    if (cmd === "START") {
      socket.emit("start_game", {
        difficulty: selectedDifficulty,
        goal: selectedGoal
      });
      let content = printHeader();
      content += "Starting market session...\n";
      content += "Loading share prices...";
      setScreenContent(content);
      return;
    }
    if (cmd.startsWith("DIFF ")) {
      const val = parseInt(cmd.slice(5));
      if (val >= 1 && val <= 4) {
        selectedDifficulty = val;
        socket.emit("refresh_lobby");
      } else {
        let content = printHeader();
        content += "Invalid difficulty. Choose 1-4.\n";
        content += "Press any key to continue...";
        setScreenContent(content);
        currentMode = "error-wait";
      }
      return;
    }
    if (cmd.startsWith("GOAL ")) {
      const val = parseInt(cmd.slice(5));
      if (!isNaN(val) && val > 0) {
        selectedGoal = val;
        socket.emit("refresh_lobby");
      } else {
        let content = printHeader();
        content += "Invalid goal amount.\n";
        content += "Press any key to continue...";
        setScreenContent(content);
        currentMode = "error-wait";
      }
      return;
    }
    let content = printHeader();
    content += `Unknown command: ${cmd}\n`;
    content += "Valid commands: DIFF [1-4], GOAL [amount], START\n";
    content += "Press any key to continue...";
    setScreenContent(content);
    currentMode = "error-wait";
    return;
  }

  if (currentMode === "error-wait") {
    socket.emit("refresh_lobby");
    return;
  }

  if (currentMode === "action") {
    // Quick buy/sell commands like BL10, SG5, etc.
    if (["BL", "BZ", "BT", "BG"].some(prefix => cmd.startsWith(prefix))) {
      const map = { BL: "LEAD", BZ: "ZINC", BT: "TIN", BG: "GOLD" };
      const prefix = cmd.slice(0, 2);
      const amount = parseInt(cmd.slice(2));
      if (!isNaN(amount)) {
        socket.emit("buy", { username, share: map[prefix], amount });
        // Removed print message - player knows what they did
        return;
      }
    }
    if (["SL", "SZ", "ST", "SG"].some(prefix => cmd.startsWith(prefix))) {
      const map = { SL: "LEAD", SZ: "ZINC", ST: "TIN", SG: "GOLD" };
      const prefix = cmd.slice(0, 2);
      const amount = parseInt(cmd.slice(2));
      if (!isNaN(amount)) {
        socket.emit("sell", { username, share: map[prefix], amount });
        // Removed print message - player knows what they did
        return;
      }
    }
    if (cmd === "B") {
      print("Which shares will you buy, Sir?");
      print("L = LEAD, Z = ZINC, T = TIN, G = GOLD, Q = cancel");
      currentMode = "buy-select";
    } else if (cmd === "S") {
      print("Which shares will you sell, Sir?");
      print("L = LEAD, Z = ZINC, T = TIN, G = GOLD");
      print("P = Pay loan, Q = cancel");
      currentMode = "sell-select";
    } else if (cmd === "Q") {
      console.log("DEBUG: User pressed Q, sending end_turn");
      socket.emit("end_turn", { username: username });
      // Removed print message - turn ending is obvious
    } else if (cmd === "HELP" || cmd === "H") {
      showHelp();
    }
  } else if (currentMode === "buy-select" || currentMode === "sell-select") {
    const map = { L: "LEAD", Z: "ZINC", T: "TIN", G: "GOLD" };
    if (cmd === "Q") {
      currentMode = "action";
      socket.emit("request_update");
      return;
    }
    if (cmd === "P" && currentMode === "sell-select") {
      print("How much do you want to repay? (0 for all)");
      currentMode = "repay-loan";
      return;
    }
    if (map[cmd]) {
      currentShare = map[cmd];
      print(`How many ${currentShare} shares will you ${currentMode === "buy-select" ? "buy" : "sell"}, Sir?`);
      currentMode = currentMode === "buy-select" ? "buy-amount" : "sell-amount";
    }
  } else if (currentMode === "repay-loan") {
    const amount = parseInt(cmd);
    if (!isNaN(amount)) {
      const repayAmount = amount === 0 ? null : amount;
      socket.emit("repay_loan", { username, amount: repayAmount });
      // Removed print message - player knows what they did
    }
    currentMode = "action";
  } else if (currentMode === "buy-amount") {
    const amount = parseInt(cmd);
    if (!isNaN(amount)) {
      socket.emit("buy", { username, share: currentShare, amount });
      // Removed print message - player knows what they did
      // Return to action mode after transaction
      currentMode = "action";
      // Request update to get fresh data
      setTimeout(() => {
        socket.emit("request_update");
      }, 100);
    } else {
      currentMode = "action";
    }
  } else if (currentMode === "sell-amount") {
    const amount = parseInt(cmd);
    if (!isNaN(amount)) {
      socket.emit("sell", { username, share: currentShare, amount });
      // Removed print message - player knows what they did
      // Return to action mode after transaction
      currentMode = "action";
      // Request update to get fresh data
      setTimeout(() => {
        socket.emit("request_update");
      }, 100);
    } else {
      currentMode = "action";
    }
  } else if (currentMode === "help-wait") {
    // Return to game after viewing help
    socket.emit("request_update");
    return;
  } else if (currentMode === "news-wait") {
    // User pressed key to dismiss news
    clearTimeout(window.newsTimeout);
    screen.classList.remove("news-flash");
    socket.emit("request_update");
    return;
  }
});

function showHelp() {
  switchToSingleColumnLayout();
  let content = printHeader();
  content += "*** HELP ***\n\n";
  content += "Commands:\n";
  content += "B = Buy shares (interactive)\n";
  content += "S = Sell shares (interactive)\n";
  content += "BL10 = Buy 10 LEAD shares (quick)\n";
  content += "SG5 = Sell 5 GOLD shares (quick)\n";
  content += "P = Pay back loan (in sell menu)\n";
  content += "Q = Quit turn\n";
  content += "H or HELP = Show this help\n\n";
  content += "Goal: Reach $" + selectedGoal.toLocaleString() + " to win!\n\n";
  content += "Press any key to continue...";
  setScreenContent(content);
  currentMode = "help-wait";
}

function drawStatus(data) {
  // Always ensure we're in two-column mode during gameplay
  switchToTwoColumnLayout();
  
  const p = data.players[username];
  let content = "";

  // Player status header
  if (p.bankrupt) {
    content += `PLAYER: ${username.toUpperCase()} - BANKRUPT\n`;
  } else {
    content += `PLAYER: ${username.toUpperCase()}\n`;
  }
  content += `ROUND ${data.round}/10\n`;
  content += "=".repeat(50) + "\n\n";

  // Left column - Player's shares and bank
  const leftLines = [];
  leftLines.push("YOUR PORTFOLIO:");
  leftLines.push("");
  const shareOrder = ["LEAD", "ZINC", "TIN", "GOLD"];
  for (const s of shareOrder) {
    const count = p.shares[s] || 0;
    leftLines.push(`${s.padEnd(6)} = ${count.toString().padStart(4)}`);
  }
  leftLines.push("");
  leftLines.push(`BALANCE = $${p.balance.toFixed(2)}`);
  if (p.loan > 0) {
    leftLines.push(`LOAN    = $${p.loan.toFixed(2)}`);
  }

  // Calculate total value
  let totalValue = p.balance - p.loan;
  for (const s of shareOrder) {
    totalValue += (p.shares[s] || 0) * (data.share_prices[s] || 0);
  }
  leftLines.push(`TOTAL   = $${totalValue.toFixed(2)}`);

  // Right column - Market prices
  const rightLines = [];
  rightLines.push("MARKET PRICES:");
  rightLines.push("");
  for (const s of shareOrder) {
    if (data.share_prices[s] !== undefined) {
      rightLines.push(`${s.padEnd(6)} = $${data.share_prices[s]}`);
    }
  }

  // Create the two-column layout
  const maxLines = Math.max(leftLines.length, rightLines.length);
  
  for (let i = 0; i < maxLines; i++) {
    const left = (leftLines[i] || "").padEnd(25);
    const right = rightLines[i] || "";
    content += `${left} ${right}\n`;
  }
  
  content += "\n" + "=".repeat(50) + "\n\n";
  content += "Commands: B=Buy S=Sell Q=Quit H=Help\n";
  content += "Quick: BL10 SG5 etc.\n";
  content += ">\n\n";
  
  // Show whose turn it is
  if (data.current_player === username) {
    content += ">>> IT'S YOUR TURN <<<\n";
  } else {
    content += `Waiting for ${data.current_player}...\n`;
    addActivityEntry("turn", `${data.current_player} is taking their turn`, data.current_player);
  }
  
  setScreenContent(content);
  currentMode = "action";
}

socket.on("activity", (data) => {
  // Only show activity that's relevant to the current player:
  // - Other players' actions (always show)
  // - News/flash news (always show)
  // - System messages (always show)
  // - Skip own trade actions (player knows what they did)
  
  const shouldShow = data.playerName !== username || 
                     data.type === "news" || 
                     data.type === "flash" || 
                     data.type === "system" ||
                     data.type === "turn";
  
  if (shouldShow) {
    addActivityEntry(data.type, data.message, data.playerName);
  }
  
  // If this is our own trading activity, request an immediate update to sync player state
  if (data.playerName === username && data.type === "trade") {
    setTimeout(() => {
      socket.emit("request_update");
    }, 50); // Very quick update
  }
});

socket.on("update", (data) => {
  // Switch to two-column layout when game starts
  if (currentMode !== "game-active") {
    switchToTwoColumnLayout();
    currentMode = "game-active";
  }
  
  // Always redraw status to ensure fresh data
  drawStatus(data);
});

socket.on("lobby", (data) => {
  isHost = (data.host_player === username);
  showLobby(data.players);
});

socket.on("message", (data) => {
  // Don't show transaction messages in activity log for current player
  // The player knows what they did, and it clutters the log
  // Only show system messages if they're errors or important info
  if (data.msg.includes("Error") || data.msg.includes("Invalid") || data.msg.includes("Cannot")) {
    addActivityEntry("system", data.msg, username);
  }
});

socket.on("game_over", (data) => {
  switchToSingleColumnLayout();
  let content = printHeader();
  content += "\n*** GAME OVER ***\n\n";
  content += "WINNERS:\n";
  data.winners.forEach(w => content += `>>> ${w} <<<\n`);
  content += "\nCongratulations!\n";
  content += "The market is now closed.\n\n";
  content += "Press F5 to play again.";
  setScreenContent(content);
});

socket.on("news", (data) => {
  // Add each market news event as a separate entry for line-by-line display
  data.events.forEach((event, index) => {
    // Add a small delay between each line to ensure proper ordering
    setTimeout(() => {
      addActivityEntry("news", event, null);
    }, index * 50); // 50ms delay between each line
  });
  
  // Set mode to wait for keypress or continue automatically
  currentMode = "news-wait";
  
  // Also clear after 10 seconds as fallback
  const newsTimeout = setTimeout(() => {
    if (currentMode === "news-wait") {
      currentMode = "action";
    }
  }, 10000);
  
  // Store timeout ID so we can clear it if user presses key
  window.newsTimeout = newsTimeout;
});

socket.on("flash_news", (data) => {
  // Add each flash news event as a separate entry for line-by-line display
  data.events.forEach((event, index) => {
    // Add a small delay between each line to ensure proper ordering
    setTimeout(() => {
      if (index === 0 && event.includes("NEWSFLASH")) {
        // First event is usually "!! NEWSFLASH !!", show it as header
        addActivityEntry("flash", event, null);
      } else {
        // Subsequent events are the actual news content
        addActivityEntry("flash", event, null);
      }
    }, index * 50); // 50ms delay between each line
  });
  
  // Brief visual flash effect on screen border (red flash for news)
  screen.classList.add("news-flash");
  setTimeout(() => {
    screen.classList.remove("news-flash");
  }, 500);
});

// Initialize the game
showIntro();
