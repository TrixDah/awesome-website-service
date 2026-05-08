from ._anvil_designer import frmLoginTemplate
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil import open_form
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import time
loginCharacterLimit = 50

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    # Always keep this line so Anvil can load your UI!
    self.init_components(**properties) 

    # 1. Catch the logged-in user row in a variable
    user_row = anvil.users.login_with_form()

    # 2. Check if they actually logged in (and didn't just hit the 'X' to close the popup)
    if user_row is not None:

      # 3. Extract the actual text from the 'Username' column in your database
      username = user_row['Username']

      # 4. NOW you can pass that defined variable to the next form!
      open_form('frmMessaging', current_user=username)
