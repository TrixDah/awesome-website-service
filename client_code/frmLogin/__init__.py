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
from anvil import alert
from ..frmUsername import frmUsername

class frmLogin(frmLoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties) 

  @handle("btnLogin", "click")
  def btnLogin_click(self, **event_args):
    user_row = anvil.users.login_with_form()
    if user_row is not None:
      username = user_row['Username']
      users = anvil.server.call('get_user_by_username', username)
      enabled = users[0]['enabled']
      print(list(users))
      if not enabled: # this is here to mitagate an anvil bug (or featue) https://anvil.works/forum/t/login-with-google-allows-user-to-login-first-time-even-though-the-new-user-accounts-can-be-used-right-away-tab-is-disabled/5506/3
        print("user not enabled!")
        self.lblErr.visible = True
        return

      if username is None:
        new_username = alert(frmUsername(), large=True, buttons=[])

      print(new_username)
      
      if new_username:
        anvil.server.call()
      else:
        return
        
      open_form('frmMessaging', current_user=username)
