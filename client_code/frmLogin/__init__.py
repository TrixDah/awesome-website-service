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

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties) 

  @handle("btnLogin", "click")
  def btnLogin_click(self, **event_args):
    user_row = anvil.users.login_with_form()
    if user_row is not None:
      username = user_row['Username']
      users = app_tables.messages.search(username=username)
      print(users)
      open_form('frmMessaging', current_user=username)
