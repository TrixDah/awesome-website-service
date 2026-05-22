import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
def delete_user_by_username(username):
    """
    deletes all links to a user in a non-cascading way to ensure no null-pointers/dangling pointers
    """
    user_row = app_tables.users.get(Username=username)
    if not user_row:
        return f"No user found with username '{username}'"

    for chat in app_tables.chats.search():
        participants = chat['Participants'] or []
        if user_row not in participants:
            continue

        if chat['ChatName'] == 'General Chat':
            chat.update(Participants=[p for p in participants if p != user_row])
        else:
            print(list(chat))
            for message in app_tables.messages.search(TargetChat=chat):
                message.delete()
            chat.delete()
           
    for message in app_tables.messages.search():
        read_by = message['ReadBy'] or []
        if user_row in read_by:
            message.update(ReadBy=[r for r in read_by if r != user_row])

    print("messages: ")
    for message_row in app_tables.messages.search(Sender=username):
        print(message_row)
        message_row.delete()

    user_row.delete()

    return f"User '{username}' deleted successfully."

@anvil.server.callable
def toggle_user(username):
    """activates a user by their username"""
    user_row = app_tables.users.get(Username=username)
    if not user_row:
        return f"No user found with username '{username}'"

    user_row['enabled'] = not user_row['enabled']
    print(f"{username} has been {'enabled' if user_row['enabled'] else 'disabled'}")