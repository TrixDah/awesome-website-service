from ._anvil_designer import frmLoginTemplate
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil import open_form
from anvil import *


class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  # Explicitly bind the click event to btnLogin
  @handle("btnLogin", "click")
  def attempt_login(self, **event_args):
    username = self.txtUsername.text
    password = self.txtPassword.text

    # Call the server to check credentials
    is_valid = anvil.server.call('verify_login', username, password)

    if is_valid:
      open_form('frmMessaging', current_user=username)
    else:
      self.lblError.text = "Invalid username or password."
      self.lblError.visible = True