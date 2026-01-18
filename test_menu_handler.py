
import unittest.mock as mock
import sys
import os
import logging
import time

# Mock the database operations before importing command_handlers
# We need to do this because command_handlers imports them at top level
sys.modules['db_operations'] = mock.MagicMock()
sys.modules['utils'] = mock.MagicMock()
sys.modules['meshtastic'] = mock.MagicMock()

# Setup basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Now import the module under test
import command_handlers

# Mock State Management
# In the real app, this is likely in a database or in-memory dict passed around.
# We will keep a local state dict to emulate `update_user_state`.
USER_STATE = {}

def mock_update_user_state(sender_id, state):
    global USER_STATE
    if state is None:
        if sender_id in USER_STATE:
            del USER_STATE[sender_id]
        print(f"[DEBUG] State cleared for {sender_id}")
    else:
        # If existing state exists, merge or replace? 
        # The real app likely replaces or updates. 
        # Looking at handlers, it seems to pass the whole new state or updates fields.
        # Let's assume it replaces or we merge if we want to be fancy, but simple assignment is likely enough for tests
        # accurately mimicking 'update' behavior usually implies merging only if it's a partial update, 
        # but in the code `update_user_state` is often called with a fresh dict.
        # Let's store what is passed.
        current = USER_STATE.get(sender_id, {})
        current.update(state)
        USER_STATE[sender_id] = current
        print(f"[DEBUG] State updated for {sender_id}: {USER_STATE[sender_id]}")

def mock_send_message(response, sender_id, interface):
    print(f"\n--- [Bot -> User {sender_id}] ---\n{response}\n-----------------------------")

def mock_get_node_id_from_num(sender_id, interface):
    return f"!{sender_id}"

def mock_get_node_short_name(node_id, interface):
    return "TEST_USER"

# Patch the imported functions in command_handlers
command_handlers.send_message = mock_send_message
command_handlers.update_user_state = mock_update_user_state
command_handlers.get_node_id_from_num = mock_get_node_id_from_num
command_handlers.get_node_short_name = mock_get_node_short_name

# Mock DB return values
command_handlers.get_mail = mock.MagicMock(return_value=[
    (1, "Friend", "Hello", "2023-10-27"),
    (2, "Admin", "System Update", "2023-10-28")
])
command_handlers.get_mail_content = mock.MagicMock(return_value=(
    "Friend", "2023-10-27", "Hello", "How are you doing today?", "unique_id_1"
))
command_handlers.get_bulletins = mock.MagicMock(return_value=[
    (1, "Sale", "UserA", "10:00"),
    (2, "Lost Dog", "UserB", "11:00")
])
command_handlers.get_bulletin_content = mock.MagicMock(return_value=(
    "UserA", "10:00", "Sale", "Selling old radio gear.", "unique_bulletin_1"
))
command_handlers.get_channels = mock.MagicMock(return_value=[
    ("MeshChat", "https://mesh.chat/xyz"),
    ("EmComm", "https://emcomm.org/grp")
])
command_handlers.add_bulletin = mock.MagicMock(return_value="new_bulletin_id")
command_handlers.add_mail = mock.MagicMock(return_value="new_mail_id")
command_handlers.add_channel = mock.MagicMock()
command_handlers.delete_mail = mock.MagicMock()

class MockInterface:
    def __init__(self):
        self.nodes = {
            '!12345': {
                'user': {'longName': 'Test User', 'shortName': 'TEST', 'hwModel': 'T-Beam', 'role': 'CLIENT'},
                'lastHeard': int(time.time()),
                'deviceMetrics': {'batteryLevel': 85}
            },
            '!99999': {
                 'user': {'longName': 'Low Battery Node', 'shortName': 'LOW', 'hwModel': 'T-Echo', 'role': 'ROUTER'},
                 'lastHeard': int(time.time()),
                 'deviceMetrics': {'batteryLevel': 10}
            }
        }
        self.allowed_nodes = ['!12345']
        self.bbs_nodes = []

def main():
    print("Starting Interactive Command Handler Test...")
    print("Simulating User: 12345")
    print("Type 'exit' to quit script.")
    print("Type a command (or press Enter to mock initial 'HELP' command if needed, though usually user triggers it).")
    
    sender_id = "12345"
    interface = MockInterface()
    
    # Initial trigger - equivalent to sending "HELP" or just connecting logic?
    # Usually a user sends a message. Let's assume blank start -> Help
    command_handlers.handle_help_command(sender_id, interface)
    
    while True:
        try:
            user_input = input(f"\n[User {sender_id}] > ").strip()
        except EOFError:
            break
            
        if user_input.lower() == 'exit':
            break
            
        # Determine how to route the message based on state
        state = USER_STATE.get(sender_id)
        
        # Simplified routing mimicking typical main loop logic
        if not state:
            # No state, treat as main menu command
            # For this test, let's map input to the main handlers manually or via the 'help' logic
            # The 'handle_help_command' shows menu but doesn't technically wait for input *in the handler*.
            # The *caller* (main loop) usually sees the next message and decides.
            # We need to mimic that "next message" logic here.
            
            # Since we don't have the main message router code, we inferred from `handle_help_command`
            # that `build_menu` suggests keys like B, U, M etc.
            # We have to guess which handler to call based on input since we don't have the router.
            # Let's make a simple router based on the menu keys seen in `build_menu`.
            
            cmd = user_input.upper()
            if cmd == 'B': # BBS
                command_handlers.handle_help_command(sender_id, interface, 'bbs')
            elif cmd == 'U': # Utilities
                command_handlers.handle_help_command(sender_id, interface, 'utilities')
            elif cmd == 'Q': # Quick
                command_handlers.handle_quick_help_command(sender_id, interface)
            elif cmd == 'X': # Exit
                 command_handlers.handle_exit_command(sender_id, interface)
                 
            # Note: The main menu shows 'M'ail in the code interpretation of `build_menu`?
            # Actually `build_menu` has mapped 'M' for mail, but `handle_help_command` for main menu 
            # uses `main_menu_items` from config.
            # Config has: Q, B, U, X. So 'M' is NOT in main menu by default in example_config.
            # However, if the user manually types 'MAIL' or something, usually there's a command parser.
            # We'll just stick to simulating what's in the menu or simple state transitions.
            
            else:
                # If unknown, maybe help again?
                command_handlers.handle_help_command(sender_id, interface)
                
        else:
            # We have state, so we route to steps handlers
            cmd_type = state.get('command')
            step = state.get('step')
            
            if cmd_type == 'MENU':
                # Submenus (BBS, Utilities) usually just display info and wait for command?
                # Actually `handle_help_command` sets step=1 for MENU. 
                # But there isn't a `handle_menu_steps` visible in the file provided...
                # Wait, looking at `handle_help_command`:
                # It sets {'command': 'MENU', 'menu': menu_name, 'step': 1}
                # But where is the code that consumes this?
                # The provided file `command_handlers.py` has `handle_stats_steps`, `handle_bb_steps`, etc.
                # It does NOT seem to have a generic `handle_menu_steps`.
                # This suggests the main loop might handle simple menu selection?
                # OR, maybe we should look at `handle_bb_steps` if we are in BBS menu.
                
                # Let's look closer at `handle_help_command`.
                # If we are in 'bbs' menu, we see options: M, B, C, J, X (from config)
                # 'B' -> Bulletin Menu -> `handle_bulletin_command`?
                # 'M' -> Mail Menu -> `handle_mail_command`?
                # 'C' -> Channel Dir -> `handle_channel_directory_command`?
                # 'S' -> Stats -> `handle_stats_command`?
                
                # Effectively, the "State" 'MENU' might just be a marker, and the main loop functionality 
                # (which we are mimicking) mimics "being in a menu" by just accepting those hotkeys.
                
                # So let's implement a mini-router for those sub-menus.
                menu_name = state.get('menu')
                inp = user_input.upper()
                
                if menu_name == 'bbs':
                     if inp == 'B': command_handlers.handle_bulletin_command(sender_id, interface)
                     elif inp == 'M': command_handlers.handle_mail_command(sender_id, interface)
                     elif inp == 'C': command_handlers.handle_channel_directory_command(sender_id, interface)
                     elif inp == 'X': command_handlers.handle_help_command(sender_id, interface) # Back/Exit
                     else: print(f"Unknown BBS command: {inp}")
                
                elif menu_name == 'utilities':
                     if inp == 'S': command_handlers.handle_stats_command(sender_id, interface)
                     elif inp == 'F': command_handlers.handle_fortune_command(sender_id, interface)
                     elif inp == 'W': command_handlers.handle_wall_of_shame_command(sender_id, interface)
                     elif inp == 'X': command_handlers.handle_help_command(sender_id, interface)
                     else: print(f"Unknown Util command: {inp}")

            elif cmd_type == 'MAIL':
                 # Route to handle_mail_steps ? 
                 # But `handle_mail_command` sets state to MAIL step 1.
                 # Then user input should go to... wait, is there a `handle_mail_steps`?
                 # Yes, `handle_mail_steps(sender_id, message, step, state, interface, bbs_nodes)`
                 command_handlers.handle_mail_steps(sender_id, user_input, step, state, interface, interface.bbs_nodes)

            elif cmd_type == 'BULLETIN_MENU':
                 # `handle_bulletin_command` sets this.
                 # The user then enters input... to where?
                 # `handle_bb_steps` seems to handle bulletin board interaction.
                 # Let's try routing there.
                 # But `handle_bulletin_command` sets 'BULLETIN_MENU' step 1.
                 # `handle_bb_steps` checks `step == 1` and expects `0`,`1`,`2`,`3` (indices of boards).
                 command_handlers.handle_bb_steps(sender_id, user_input, step, state, interface, interface.bbs_nodes)
                 
            elif cmd_type in ['BULLETIN_ACTION', 'BULLETIN_READ', 'BULLETIN_POST', 'BULLETIN_POST_CONTENT']:
                 # All these seem handled by `handle_bb_steps`
                 command_handlers.handle_bb_steps(sender_id, user_input, step, state, interface, interface.bbs_nodes)
                 
            elif cmd_type == 'STATS':
                 command_handlers.handle_stats_steps(sender_id, user_input, step, interface)
                 
            elif cmd_type == 'CHANNEL_DIRECTORY':
                 command_handlers.handle_channel_directory_steps(sender_id, user_input, step, state, interface)
                 
            elif cmd_type == 'CHECK_MAIL':
                 if step == 1:
                     command_handlers.handle_read_mail_command(sender_id, user_input, state, interface)
                 elif step == 2:
                     command_handlers.handle_delete_mail_confirmation(sender_id, user_input, state, interface, interface.bbs_nodes)
            
            else:
                 print(f"Unknown state command type: {cmd_type}")
                 # Fallback to main menu?
                 command_handlers.handle_help_command(sender_id, interface)

if __name__ == "__main__":
    main()
