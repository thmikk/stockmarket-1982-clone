#!/usr/bin/env python3
"""
Test script that simulates real multiplayer scenario
"""

import socketio
import time

def test_multiplayer_scenario():
    """Test multiplayer scenario with real SocketIO"""
    
    # Create client connections
    client1 = socketio.Client()
    client2 = socketio.Client()
    
    try:
        # Connect clients
        print("Connecting clients...")
        client1.connect('http://localhost:5000')
        client2.connect('http://localhost:5000')
        
        # Join game
        print("Player1 joining...")
        client1.emit('join', {'username': 'TestPlayer1'})
        time.sleep(0.1)
        
        print("Player2 joining...")
        client2.emit('join', {'username': 'TestPlayer2'})
        time.sleep(0.1)
        
        # Start game
        print("Starting game...")
        client1.emit('start_game', {'difficulty': 1, 'goal': 1000000})
        time.sleep(0.1)
        
        # Player1 ends turn
        print("Player1 ending turn...")
        client1.emit('end_turn', {'username': 'TestPlayer1'})
        time.sleep(0.5)  # Wait a bit for processing
        
        # Player2 ends turn (should trigger market news)
        print("Player2 ending turn...")
        client2.emit('end_turn', {'username': 'TestPlayer2'})
        time.sleep(0.5)  # Wait a bit for processing
        
        print("Test completed. Check server logs for duplicate news.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            client1.disconnect()
            client2.disconnect()
        except:
            pass

if __name__ == "__main__":
    test_multiplayer_scenario()
