from ._anvil_designer import frmLoginTemplate
import anvil.server
from anvil import open_form, *
import anvil.users

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties) 

  @handle("btnLogin", "click")
  def btnLogin_click(self, **event_args):
    """Handle login button click - authenticate and open messaging form."""
    user_row = anvil.users.login_with_form()
    if user_row is not None:
      open_form('frmMessaging', current_user=user_row['Username'])
