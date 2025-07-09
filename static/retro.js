const socket = io();
let username = null;
let gameState = 'boot';
const log = document.getElementById('log');
const commandInput = document.getElementById('command-input');

// Utility functions
function appendToLog(text, className = '') {
    const div = document.createElement('div');
    div.textContent = text;
    if (className) div.className = className;
    log.appendChild(div);
    // Scroll to bottom
    log.scrollTop = log.scrollHeight;
}

function clearLog() {
    log.innerHTML = '';
}

function showPrompt() {
    appendToLog('\n> ', 'prompt');
}

function displayHelp(state) {
    switch(state) {
        case 'lobby':
            appendToLog('\nCommands:', 'info-text');
            appendToLog('  START - Begin the game (host only)', 'info-text');
            break;
        case 'game':
            appendToLog('\nCommands:', 'info-text');
            appendToLog('  BUY <share> <amount> - Buy shares', 'info-text');
            appendToLog('  SELL <share> <amount> - Sell shares', 'info-text');
            appendToLog('  END - End your turn', 'info-text');
            appendToLog('Available shares: LEAD, ZINC, TIN, GOLD', 'info-text');
            break;
    }
}

// Connection handling
socket.on('connect', () => {
    console.log('Connected to server');
    appendToLog('CONNECTING TO MARKET...', 'info-text');
});

socket.on('disconnect', () => {
    appendToLog('\n*** CONNECTION LOST ***', 'error-text');
    gameState = 'error';
});

socket.on('connection_success', (data) => {
    console.log('Connection successful');
    gameState = 'login';
    appendToLog('\nWelcome to STOCKMARKET 1982!', 'success-text');
    appendToLog('Please enter your name (2-12 characters):', 'info-text');
    showPrompt();
});

// Command handling
commandInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        const command = this.value.trim().toUpperCase();
        this.value = '';
        
        // Echo the command
        appendToLog(`${command}`, 'input-text');

        if (!command) {
            showPrompt();
            return;
        }

        if (command === 'HELP') {
            displayHelp(gameState);
            showPrompt();
            return;
        }

        switch (gameState) {
            case 'login':
                if (command.length < 2 || command.length > 12) {
                    appendToLog('\nName must be 2-12 characters long', 'error-text');
                    showPrompt();
                    return;
                }
                username = command;
                socket.emit('join', { username });
                appendToLog(`\nWelcome ${username}! Connecting to market...`, 'success-text');
                gameState = 'connecting';
                break;

            case 'lobby':
                if (command === 'START') {
                    socket.emit('start_game', { 
                        username: username,
                        difficulty: 1,
                        goal: 1000000
                    });
                } else {
                    appendToLog('\nInvalid command. Type HELP for commands.', 'error-text');
                    showPrompt();
                }
                break;

            case 'game':
                const parts = command.split(' ');
                
                // Check if it's the player's turn
                if (username !== currentPlayer) {
                    appendToLog("\nIt's not your turn!", 'error-text');
                    appendToLog(`Waiting for ${currentPlayer} to play...`, 'info-text');
                    return;
                }
                
                switch (parts[0]) {
                    case 'BUY':
                        if (parts.length === 3 && !isNaN(parts[2])) {
                            socket.emit('buy', {
                                username: username,
                                share: parts[1],
                                amount: parseInt(parts[2])
                            });
                        } else {
                            appendToLog('\nUsage: BUY <share> <amount>', 'error-text');
                            showPrompt();
                        }
                        break;
                        
                    case 'SELL':
                        if (parts.length === 3 && !isNaN(parts[2])) {
                            socket.emit('sell', {
                                username: username,
                                share: parts[1],
                                amount: parseInt(parts[2])
                            });
                        } else {
                            appendToLog('\nUsage: SELL <share> <amount>', 'error-text');
                            showPrompt();
                        }
                        break;
                        
                    case 'END':
                        socket.emit('end_turn', { username });
                        break;
                        
                    default:
                        appendToLog('\nInvalid command. Type HELP for commands.', 'error-text');
                        showPrompt();
                }
                break;
        }
    }
});

// Game event handlers
socket.on('lobby', (data) => {
    if (gameState === 'connecting') {
        clearLog();
        appendToLog('STOCKMARKET 1982 - LOBBY\n', 'success-text');
    }
    
    appendToLog('\nPlayers connected:', 'info-text');
    data.players.forEach(player => {
        appendToLog(`  ${player}${player === data.host_player ? ' (Host)' : ''}`);
    });
    
    if (data.host_player === username) {
        appendToLog('\nYou are the host! Type START to begin the game', 'success-text');
    } else {
        appendToLog('\nWaiting for host to start the game...', 'info-text');
    }
    
    gameState = 'lobby';
    appendToLog('\nType HELP for commands', 'info-text');
    showPrompt();
});

let currentPlayer = null;

socket.on('update', (data) => {
    if (gameState !== 'game') {
        gameState = 'game';
        clearLog();
        appendToLog('STOCKMARKET 1982 - GAME IN PROGRESS\n', 'success-text');
    }
    
    currentPlayer = data.current_player;
    
    appendToLog(`\nRound ${data.round}, Turn ${data.turn}`, 'info-text');
    appendToLog(`Current player: ${currentPlayer}`, currentPlayer === username ? 'success-text' : 'info-text');
    
    appendToLog('\nShare prices:', 'market-prices');
    Object.entries(data.share_prices).forEach(([share, price]) => {
        appendToLog(`  ${share}: $${price}`);
    });
    
    appendToLog('\nPlayers:', 'player-list');
    Object.entries(data.players).forEach(([name, info]) => {
        let shares = Object.entries(info.shares)
            .map(([s,n]) => `${s}:${n}`)
            .join(', ');
        let highlight = name === currentPlayer ? 'success-text' : '';
        appendToLog(`  ${name}: $${info.cash} (${shares})`, highlight);
    });
    
    if (currentPlayer === username) {
        appendToLog('\nIt\'s your turn! Type HELP for commands', 'success-text');
        showPrompt();
    } else {
        appendToLog(`\nWaiting for ${currentPlayer} to play...`, 'info-text');
    }
});

socket.on('message', (data) => {
    appendToLog(`\n${data.msg}`, 'info-text');
    if (gameState === 'game') {
        showPrompt();
    }
});

socket.on('flash_news', (data) => {
    data.events.forEach(event => {
        appendToLog(`\nFLASH NEWS: ${event}`, 'error-text');
    });
    if (gameState === 'game') {
        showPrompt();
    }
});

socket.on('game_over', function(data) {
    let winner = data.winner;
    displayMessage(`*** GAME OVER ***\n${winner} WINS THE GAME!\nAll other players are bankrupt.`, 'system');
    // Disable all game controls
    document.getElementById('commandInput').disabled = true;
});

function handleLobbyCommand(command) {
    const cmd = command.toUpperCase();
    if (cmd === 'START') {
        socket.emit('start_game', { difficulty: 1, goal: 1000000 });
    } else {
        appendToLog('Invalid command. Wait for game to start...', 'error-text');
    }
}

function handleGameCommand(command) {
    const cmd = command.toUpperCase().split(' ');
    
    switch (cmd[0]) {
        case 'BUY':
            if (cmd.length === 3) {
                socket.emit('buy', {
                    username: username,
                    share: cmd[1],
                    amount: parseInt(cmd[2])
                });
            } else {
                appendToLog('Usage: BUY <share> <amount>', 'error-text');
            }
            break;
            
        case 'SELL':
            if (cmd.length === 3) {
                socket.emit('sell', {
                    username: username,
                    share: cmd[1],
                    amount: parseInt(cmd[2])
                });
            } else {
                appendToLog('Usage: SELL <share> <amount>', 'error-text');
            }
            break;
            
        case 'END':
            socket.emit('end_turn', { username });
            break;
            
        default:
            appendToLog('Invalid command. Available commands: BUY, SELL, END', 'error-text');
    }
}
