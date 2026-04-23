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
    return None 

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