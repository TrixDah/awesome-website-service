from ._anvil_designer import frmLoginTemplate
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil import open_form
from anvil import *
import time
loginCharacterLimit = 50

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.last_login_attempt = 0
    anvil.server.call('migrate_plain_text_passwords')

  # Explicitly bind the click event to btnLogin
  @handle("btnLogin", "click")
  def attempt_login(self, **event_args):
    # 2. Check the throttle cooldown
    current_time = time.time()
    cooldown = 3 # seconds
  
    if current_time - self.last_login_attempt < cooldown:
      self.lblError.text = "Please wait a few seconds before trying again."
      self.lblError.visible = True
      return 
  
      # Update the tracker with the new time
    self.last_login_attempt = current_time
  
    username = self.txtUsername.text
    password = self.txtPassword.text
  
    #Check to ensure password and username is not too long, to prevent malicious actors.
    if len(password) >= loginCharacterLimit or len(username) >= loginCharacterLimit:
      self.lblError.text = "Input length too long. Nice try Rory."
      self.lblError.visible = True
  
      # Call the server to check credentials (server handles hashing).
    # Call the server to check credentials (server handles hashing).
    else:
      # Use the button's explicit name instead of event_args['sender']
      self.btnLogin.enabled = False

      try:
        is_valid = anvil.server.call('verify_login', username, password)
        if is_valid:
          open_form('frmMessaging', current_user=username)
        else:
          self.lblError.text = "Invalid username or password."
          self.lblError.visible = True
      finally:
        # Re-enable the button explicitly
        self.btnLogin.enabled = True

  @handle("txtPassword", "pressed_enter")
  def txtPassword_pressed_enter(self, **event_args):
    """This method is called when the user presses Enter in this text box"""
    self.attempt_login() # simulate a send button click