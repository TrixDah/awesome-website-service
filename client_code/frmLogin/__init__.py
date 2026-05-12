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
  def __init__(self, tos_accepted=None, **properties):
    self.init_components(**properties) 
    self.tos_accepted = tos_accepted

    if not tos_accepted and tos_accepted is not None:
        self.lblErr.visible = True
        self.lblErr.text = "You cannot login unless you accept the TOS."

    if tos_accepted:
        self.btnLogin_click()

  @handle("btnLogin", "click")
  def btnLogin_click(self, **event_args):
    if not self.tos_accepted:
        open_form('frmTOS')
    else:
        user_row = anvil.users.login_with_form()
        if user_row is not None:
          username = user_row['Username']
          email = user_row['email']
          users = anvil.server.call('get_user_by_email', email)
          print(users)
          enabled = users['enabled']
          if not enabled: # this is here to mitagate an anvil bug (or featue idk) 
            print("User not enabled!")
            self.lblErr.visible = True
            self.lblErr.text = "This account has not been enabled by an admin! A request has been sent."
                return
        
            if username is None:
                new_username = alert(frmUsername(), large=True, buttons=[])
                shared_username = anvil.server.call('search_for_dupes', new_username)
                print(new_username, shared_username)
                impact = len(shared_username)
                if impact > 0:
                    self.lblErr.visible = True
                    self.lblErr.text = "That username is taken. Sorry!"
                    return
            
                if new_username:
                    anvil.server.call('add_username', user_row, new_username)
                    username = new_username
                else:
                    return
                
            open_form('frmMessaging', current_user=username)
