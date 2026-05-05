from ._anvil_designer import frmLoginTemplate
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil import open_form
from anvil import *
loginCharacterLimit = 50

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    anvil.server.call('migrate_plain_text_passwords')

  # Explicitly bind the click event to btnLogin
  @handle("btnLogin", "click")
  def attempt_login(self, **event_args):
    username = self.txtUsername.text
    password = self.txtPassword.text


    #Check to ensure password and username is not too long, to prevent malicious actors.
    if len(password) >= loginCharacterLimit or len(username) >= loginCharacterLimit:
      self.lblError.text = "Input length too long. Nice try Rory."
      self.lblError.visible = True

    # Call the server to check credentials (server handles hashing).
    else:
      is_valid = anvil.server.call('verify_login', username, password)
      if is_valid:
        open_form('frmMessaging', current_user=username)
      else:
        self.lblError.text = "Invalid username or password."
        self.lblError.visible = True

  @handle("txtPassword", "pressed_enter")
  def txtPassword_pressed_enter(self, **event_args):
    """This method is called when the user presses Enter in this text box"""
    self.attempt_login() # simulate a send button click