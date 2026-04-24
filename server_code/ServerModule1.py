import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from datetime import datetime, timezone


@anvil.server.callable
def verify_login(username, password):
  user = app_tables.users.get(Username=username, Password=password)
  return True if user else False

@anvil.server.callable
def get_user_chats(username):
  user_row = app_tables.users.get(Username=username)
  return app_tables.chats.search(Participants=[user_row])

@anvil.server.callable
def create_chat(current_username, target_username):
  user1 = app_tables.users.get(Username=current_username)
  user2 = app_tables.users.get(Username=target_username)

  if not user2:
    return None # Target user doesn't exist

    # --- NEW LOGIC: Check for an existing DM ---
    # First, get all chats that user1 is a part of
  user1_chats = app_tables.chats.search(Participants=[user1])

  for chat in user1_chats:
    participants = chat['Participants']
    # If a chat has exactly 2 people, and user2 is one of them...
    if len(participants) == 2 and user2 in participants:
      return chat # We found it! Return the existing chat immediately.
    # -------------------------------------------

    # If the code makes it down here, no existing chat was found, so we create a new one.
  chat_name = f"Chat with {target_username}"
  new_chat = app_tables.chats.add_row(
    ChatName=chat_name,
    Participants=[user1, user2]
  )
  return new_chat

@anvil.server.callable
def get_chat_messages(chat_row):
  return app_tables.messages.search(
    tables.order_by("TimeSent"), 
    TargetChat=chat_row
  )

@anvil.server.callable
def send_message(sender, message_text, chat_row):
  app_tables.messages.add_row(
    Sender=sender,
    MessageText=message_text,
    TimeSent=datetime.now(timezone.utc),
    TargetChat=chat_row 
  )

@anvil.server.callable
def get_general_chat(username):
  user_row = app_tables.users.get(Username=username)

    # Check if a chat specifically named "General Chat" exists
  general_chat = app_tables.chats.get(ChatName="General Chat")

    # If the app is brand new and it doesn't exist yet, create it!
  if not general_chat:
    general_chat = app_tables.chats.add_row(
      ChatName="General Chat",
      Participants=[user_row]
      )
  else:
      # If it exists, ensure this specific user is in the Participants list
    participants = general_chat['Participants']
    if user_row not in participants:
      general_chat['Participants'] = participants + [user_row]

  return general_chat