import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from datetime import datetime, timezone
from datetime import timedelta
import anvil.tables.query as q
import hashlib

message_lifetime_hours: int = 48

@anvil.server.background_task
def scheduled_prune_messages():
  """This function will be triggered by Anvil's scheduler."""
  cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

  old_messages = app_tables.messages.search(
    TimeSent=q.less_than(cutoff)
  )

  for msg in old_messages:
    msg.delete()

@anvil.server.callable
def verify_login(username, password):
  """Verify login credentials. Password is hashed on receipt."""
  password_hash = hashlib.sha256(password.encode()).hexdigest()
  user = app_tables.users.get(Username=username, Password=password_hash)
  return True if user else False

@anvil.server.callable
def get_usernames():
  return [row['Username'] for row in app_tables.users.search()]

@anvil.server.callable
def create_user(username: str, password: str):
  """Create a new user with a hashed password."""

  # basic validation
  if not username or not password:
    return {"success": False, "error": "Username and password required"}

  # normalize username (optional but recommended)
  username = username.strip()

  # check if user already exists
  existing = app_tables.users.get(Username=username)
  if existing:
    return {"success": False, "error": "User already exists"}

  # hash password
  password_hash = hashlib.sha256(password.encode()).hexdigest()

  # add to database
  new_row = app_tables.users.add_row(
    Username=username,
    Password=password_hash
  )

  return {"success": True, "user_id": new_row.get_id()}


@anvil.server.callable
def migrate_plain_text_passwords():
  """Migration: Hash all plain text passwords in the users table.
  Run this ONCE to upgrade existing users to the new hashed password format.
  """
  all_users = app_tables.users.search()
  migrated_count = 0

  for user in all_users:
    password = user['Password']
    # Skip if already hashed (SHA256 produces 64-char hex strings)
    if len(password) == 64 and all(c in '0123456789abcdef' for c in password):
      continue

    # Hash the plain text password and update
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user['Password'] = password_hash
    migrated_count += 1

  return f"Migration complete. {migrated_count} users migrated to hashed passwords."

@anvil.server.callable
def get_user_chats(username):
  user_row = app_tables.users.get(Username=username)
  return app_tables.chats.search(Participants=[user_row])

@anvil.server.callable
def create_chat(current_username, target_username):
  user1 = app_tables.users.get(Username=current_username)
  user2 = app_tables.users.get(Username=target_username)

  if not user2:
    return None  # Target user doesn't exist

  # --- NEW LOGIC: Check for an existing DM ---
  # First, get all chats that user1 is a part of
  user1_chats = app_tables.chats.search(Participants=[user1])

  for chat in user1_chats:
    participants = chat['Participants']
    # If a chat has exactly 2 people, and user2 is one of them...
    if len(participants) == 2 and user2 in participants:
      return chat  # We found it! Return the existing chat immediately.
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

  