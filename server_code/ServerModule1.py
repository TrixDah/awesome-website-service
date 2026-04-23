import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime, timezone
from anvil import *

@anvil.server.callable
def verify_login(username, password):
  # Searches the manually created 'Users' table
  # Make sure your columns are named exactly 'Username' and 'Password'
  user = app_tables.users.get(Username=username, Password=password)
  if user:
    return True
  return False

@anvil.server.callable
def get_messages():
  # Returns all messages from the 'Messages' table, sorted oldest to newest
  # Make sure your column is named exactly 'TimeSent'
  return app_tables.messages.search(tables.order_by("TimeSent"))

@anvil.server.callable
def send_message(sender, message_text):
  # Adds a new row to the 'Messages' table
  # Make sure your columns are named exactly 'Sender', 'MessageText', and 'TimeSent'
  app_tables.messages.add_row(
    Sender=sender,
    MessageText=message_text,
    TimeSent=datetime.now(timezone.utc)
  )