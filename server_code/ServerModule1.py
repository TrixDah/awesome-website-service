import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from datetime import datetime, timezone, timedelta
import anvil.tables.query as q
import hashlib
import re

# Configuration Constants
MESSAGE_LIFETIME_HOURS = 168  # Change this to set message deletion time threshold
MESSAGE_TIMEOUT_MINUTES = 5
MESSAGE_SPAM_THRESHOLD = 10
MESSAGE_SPAM_WINDOW_MINUTES = 1
SHA256_HEX_PATTERN = re.compile(r'^[a-f0-9]{64}$')

def _hash_password(password):
  """Helper: Hash a password using SHA256."""
  return hashlib.sha256(password.encode()).hexdigest()

def _is_hashed_password(password):
  """Helper: Check if a password is already hashed (SHA256 hex format)."""
  return SHA256_HEX_PATTERN.match(password) is not None

def _get_user_by_username(username):
  """Helper: Retrieve user by username."""
  return app_tables.users.get(Username=username)

def _get_chat_last_activity(chat):
  """Helper: Get or calculate the last activity time for a chat."""
  last_act = chat['LastActivity']
  
  if last_act:
    return last_act
  
  # Find the most recent message in this chat
  recent_msgs = app_tables.messages.search(
    tables.order_by("TimeSent", ascending=False),
    TargetChat=chat
  )
  
  if recent_msgs:
    last_act = recent_msgs[0]['TimeSent']
    chat['LastActivity'] = last_act  # Auto-heal the database
    return last_act
  
  # No messages: push to bottom
  return datetime.min.replace(tzinfo=timezone.utc)

def _count_unread_messages(chat, user_row, username):
  """Helper: Count unread messages in a chat for a user."""
  messages_in_chat = app_tables.messages.search(TargetChat=chat)
  unread_count = 0
  
  for msg in messages_in_chat:
    if msg['Sender'] == username:
      continue  # Sender never has unread messages
    
    reader_ids = [r.get_id() for r in (msg['ReadBy'] or [])]
    if user_row.get_id() not in reader_ids:
      unread_count += 1
  
  return unread_count

@anvil.server.background_task
def scheduled_prune_messages():
  """This function will be triggered by Anvil's scheduler."""
  cutoff = datetime.now(timezone.utc) - timedelta(hours=MESSAGE_LIFETIME_HOURS)
  old_messages = app_tables.messages.search(TimeSent=q.less_than(cutoff))
  
  for msg in old_messages:
    msg.delete()

@anvil.server.callable
def verify_login(username, password):
  """Verify login credentials. Password is hashed on receipt."""
  password_hash = _hash_password(password)
  return bool(_get_user_by_username(username) and 
              _get_user_by_username(username)['Password'] == password_hash)

@anvil.server.callable
def get_usernames(logged_in_user: str):
  """Get all usernames except the logged-in user."""
  return [row['Username'] for row in app_tables.users.search()
          if row['Username'] != logged_in_user]

@anvil.server.callable
def create_user(username: str, password: str):
  """Create a new user with a hashed password."""
  if not username or not password:
    return {"success": False, "error": "Username and password required"}
  
  username = username.strip()
  
  if _get_user_by_username(username):
    return {"success": False, "error": "User already exists"}
  
  new_row = app_tables.users.add_row(
    Username=username,
    Password=_hash_password(password)
  )
  
  return {"success": True, "user_id": new_row.get_id()}

@anvil.server.callable
def migrate_plain_text_passwords():
  """Migration: Hash all plain text passwords in the users table.
  Run this ONCE to upgrade existing users to the new hashed password format.
  """
  migrated_count = 0
  
  for user in app_tables.users.search():
    if not _is_hashed_password(user['Password']):
      user['Password'] = _hash_password(user['Password'])
      migrated_count += 1
  
  return f"Migration complete. {migrated_count} users migrated to hashed passwords."

@anvil.server.callable
def get_user_chats_data(username):
  """Fetches chats, sorts them, adds users to General, and counts unreads."""
  user_row = _get_user_by_username(username)
  
  # Handle General Chat automatically
  general_chat = app_tables.chats.get(ChatName="General Chat")
  if general_chat:
    participants = general_chat['Participants'] or []
    if user_row not in participants:
      general_chat['Participants'] = participants + [user_row]
  
  # Get all chats this user is a part of
  all_my_chats = app_tables.chats.search(Participants=[user_row])
  chat_list = []
  
  for chat in all_my_chats:
    unread_count = _count_unread_messages(chat, user_row, username)
    last_act = _get_chat_last_activity(chat)
    
    chat_list.append({
      'chat_row': chat,
      'chat_name': chat['ChatName'] or "Direct Message",
      'last_activity': last_act,
      'unread_count': unread_count,
      'is_general': chat['ChatName'] == "General Chat"
    })
  
  # Sort: General Chat first, then by LastActivity descending
  chat_list.sort(key=lambda x: (not x['is_general'], x['last_activity']), reverse=True)
  return chat_list

@anvil.server.callable
def mark_chat_read(chat_row, username):
  """Adds the user to the ReadBy list for all messages in a chat."""
  user_row = _get_user_by_username(username)
  
  for msg in app_tables.messages.search(TargetChat=chat_row):
    readers = msg['ReadBy'] or []
    if user_row not in readers:
      msg['ReadBy'] = readers + [user_row]

@anvil.server.callable
def create_chat(current_username, target_username):
  """Create a new DM or return existing one."""
  user1 = _get_user_by_username(current_username)
  user2 = _get_user_by_username(target_username)
  
  if not user2:
    return None  # Target user doesn't exist
  
  # Check for existing DM between these users
  for chat in app_tables.chats.search(Participants=[user1]):
    participants = chat['Participants']
    if len(participants) == 2 and user2 in participants:
      return chat  # Found existing DM
  
  # Create new DM
  new_chat = app_tables.chats.add_row(
    ChatName=f"Chat with {target_username}",
    Participants=[user1, user2]
  )
  return new_chat

@anvil.server.callable
def get_chat_messages(chat_row):
  """Retrieve all messages in a chat, ordered by time."""
  return app_tables.messages.search(
    tables.order_by("TimeSent"),
    TargetChat=chat_row
  )

@anvil.server.callable
def send_message(sender_username, message_text, chat_row, image_file=None):
  """Send a message with optional image and anti-spam protection."""
  now = datetime.now(timezone.utc)
  user_row = _get_user_by_username(sender_username)
  
  if not user_row:
    return {"success": False, "error": "Error: User account not found."}
  
  # Check timeout
  timeout_end = user_row.get('timeout_until')
  if timeout_end and timeout_end > now:
    mins_left = int((timeout_end - now).total_seconds() / 60) + 1
    return {"success": False, "error": f"You are timed out. Please wait {mins_left} minutes."}
  
  # Check spam
  recent_messages = app_tables.messages.search(
    Sender=sender_username,
    TimeSent=q.greater_than(now - timedelta(minutes=MESSAGE_SPAM_WINDOW_MINUTES))
  )
  
  if len(recent_messages) >= MESSAGE_SPAM_THRESHOLD:
    user_row['timeout_until'] = now + timedelta(minutes=MESSAGE_TIMEOUT_MINUTES)
    return {"success": False, "error": f"Spam detected. You are timed out for {MESSAGE_TIMEOUT_MINUTES} minutes."}
  
  # Save message
  app_tables.messages.add_row(
    Sender=sender_username,
    MessageText=message_text,
    TimeSent=now,
    TargetChat=chat_row,
    MessageImage=image_file,
    ReadBy=[user_row]
  )
  chat_row['LastActivity'] = now
  
  return {"success": True}
