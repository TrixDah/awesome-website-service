import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from datetime import datetime, timezone
from datetime import timedelta
import anvil.tables.query as q
import hashlib
import secrets
from dataclasses import dataclass

message_lifetime_hours: int = 168 #Change this to set message deletion time threshold 

@anvil.server.background_task
def scheduled_prune_messages():
  """Prune expired messages and old tokens."""

  now = datetime.now(timezone.utc)

  cutoff = now - timedelta(hours=message_lifetime_hours)

  old_messages = app_tables.messages.search(
    TimeSent=q.less_than(cutoff)
  )

  for msg in old_messages:
    msg.delete()

  all_tokens = app_tables.tokens.search()

  for token_row in all_tokens:
    created_at = token_row["created_at"]
    lifetime = token_row["lifetime"]

    if not created_at or lifetime is None:
      token_row.delete()
      continue

    expiry_time = created_at + timedelta(minutes=lifetime)

    prune_time = expiry_time + timedelta(hours=1)

    if now > prune_time:
      token_row.delete()

@anvil.server.callable
def verify_login(username, password):
  """Verify login credentials. Password is hashed on receipt."""
  password_hash = hashlib.sha256(password.encode()).hexdigest()
  user = app_tables.users.get(Username=username, Password=password_hash)
  return True if user else False

@anvil.server.callable
def get_usernames(logged_in_user: str):
  return [
    row['Username']
    for row in app_tables.users.search()
    if row['Username'] != logged_in_user
  ]

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
def get_user_chats_data(username):
  """Fetches chats, sorts them, adds users to General, and counts unreads."""
  user_row = app_tables.users.get(Username=username)

  # 1. Handle General Chat automatically
  general_chat = app_tables.chats.get(ChatName="General Chat")
  if general_chat is not None:
    # If the user isn't in General Chat's participant list, add them!
    participants = general_chat['Participants'] or []
    if user_row not in participants:
      general_chat['Participants'] = participants + [user_row]

    # 2. Get all chats this user is a part of
  all_my_chats = app_tables.chats.search(Participants=[user_row])
  chat_list = []
  
  for chat in all_my_chats:
    # Fetch the messages for this chat
    messages_in_chat = app_tables.messages.search(TargetChat=chat)
    unread_count = 0

    for m in messages_in_chat:
      # THE FIX: If this user sent the message, ignore it! It is never "unread" to them.
      if m['Sender'] == username: 
        continue

      readers = m['ReadBy'] or []

      # Extract the unique ID of every reader, and check if our user's ID is missing
      reader_ids = [r.get_id() for r in readers]
      if user_row.get_id() not in reader_ids:
        unread_count += 1

    # THE FIX: Figure out the real last activity date
    last_act = chat['LastActivity']

    if not last_act: # If the column is blank (like in your older chats)
      # Find the most recent message in this chat
      recent_msgs = app_tables.messages.search(
        tables.order_by("TimeSent", ascending=False), 
        TargetChat=chat
      )
      if len(recent_msgs) > 0:
        last_act = recent_msgs[0]['TimeSent']
        # Auto-heal the database so it doesn't have to look this up next time!
        chat['LastActivity'] = last_act 
      else:
        # If there are literally no messages, push it to the very bottom
        last_act = datetime.min.replace(tzinfo=timezone.utc)

    chat_list.append({
      'chat_row': chat,
      'chat_name': chat['ChatName'] or "Direct Message", 
      'last_activity': last_act, # Use our newly calculated date!
      'unread_count': unread_count,
      'is_general': chat['ChatName'] == "General Chat"
    })

    # 4. Sort the list: General Chat always first, then by LastActivity descending
  chat_list.sort(key=lambda x: (x['is_general'], x['last_activity']), reverse=True)
  return chat_list

@anvil.server.callable
def mark_chat_read(chat_row, username):
  """Adds the user to the ReadBy list for all messages in a chat."""
  user_row = app_tables.users.get(Username=username)
  unread_messages = app_tables.messages.search(TargetChat=chat_row)

  for msg in unread_messages:
    readers = msg['ReadBy'] or []
    if user_row not in readers:
      msg['ReadBy'] = readers + [user_row]

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
def send_message(sender_username, message_text, chat_row, image_file=None):
  now = datetime.now(timezone.utc)
  user_row = app_tables.users.get(Username=sender_username)
  
  if user_row is None:
    return {"success": False, "error": "Error: User account not found."}
  
  timeout_end = user_row.get('timeout_until') 
  if timeout_end is not None and timeout_end > now:
    mins_left = int((timeout_end - now).total_seconds() / 60) + 1
    return {"success": False, "error": f"You are timed out. Please wait {mins_left} minutes."}
  
  one_minute_ago = now - timedelta(minutes=1)
  recent_messages = app_tables.messages.search(
    Sender=sender_username,
    TimeSent=q.greater_than(one_minute_ago)
  )
  
  if len(recent_messages) >= 10:
    user_row['timeout_until'] = now + timedelta(minutes=5)
    return {"success": False, "error": "Spam detected. You are timed out for 5 minutes."}
  
  # Save the message AND the image
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

@anvil.server.callable
def get_user_by_username(username: str):
  return app_tables.users.search(Username=username)

@anvil.server.callable
def delete_user(username):
  """
  deletes a user and deletes any links to them in a non-cascading way. does not delete their chats
  """

  user_row = app_tables.users.get(Username=username)

  if user_row is None:
    print("User not found")
    return

  user_id = user_row.get_id()

  # scan every table
  for table_name in dir(app_tables):

    if table_name.startswith("_"):
      continue

    table = getattr(app_tables, table_name)

    try:
      rows = list(table.search())
    except Exception:
      continue

    for row in rows:

      should_delete = False

      for col in table.list_columns():

        col_name = col['name']

        try:
          value = row[col_name]
        except Exception:
          continue

          # =================================================
          # SPECIAL CASE:
          # messages.ReadBy -> REMOVE USER ONLY
          # =================================================
        if table_name == "messages" and col_name == "ReadBy":

          if isinstance(value, list):

            cleaned = []

            for linked_user in value:

              try:
                if (
                  linked_user is not None and
                  linked_user.get_id() != user_id
                ):
                  cleaned.append(linked_user)

              except Exception:
                pass

            row[col_name] = cleaned

          elif value is not None:

            try:
              if value.get_id() == user_id:
                row[col_name] = None
            except Exception:
              pass

          continue

          # =================================================
          # SPECIAL CASE:
          # Chats.general chat -> REMOVE USER ONLY
          # =================================================
        if table_name == "Chats" and col_name == "general chat":

          if isinstance(value, list):

            cleaned = []

            for linked_user in value:

              try:
                if (
                  linked_user is not None and
                  linked_user.get_id() != user_id
                ):
                  cleaned.append(linked_user)

              except Exception:
                pass

            row[col_name] = cleaned

          elif value is not None:

            try:
              if value.get_id() == user_id:
                row[col_name] = None
            except Exception:
              pass

          continue

          # =================================================
          # messages table:
          # delete ANY message linked to this user
          # except ReadBy handled above
          # =================================================
        if table_name == "messages":

          # multi-link
          if isinstance(value, list):

            for item in value:

              try:
                if (
                  item is not None and
                  item.get_id() == user_id
                ):
                  should_delete = True
                  break

              except Exception:
                pass

                # single-link
          else:

            try:
              if (
                value is not None and
                value.get_id() == user_id
              ):
                should_delete = True

            except Exception:
              pass

          if should_delete:
            break

          continue

          # =================================================
          # ALL OTHER TABLES
          # delete rows containing user
          # =================================================
        if isinstance(value, list):

          for item in value:

            try:
              if (
                item is not None and
                item.get_id() == user_id
              ):
                should_delete = True
                break

            except Exception:
              pass

        else:

          try:
            if (
              value is not None and
              value.get_id() == user_id
            ):
              should_delete = True

          except Exception:
            pass

        if should_delete:
          break

      if should_delete:
        print(f"Deleting row from {table_name}")
        row.delete()

    # finally delete user itself
  # user_row.delete()

  print(f"Deleted user '{username}' successfully")

@anvil.server.callable
def add_username(user_R)