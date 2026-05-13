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
    def __init__(self, allowed_tos=None, **properties):
        self.init_components(**properties) 
        self.allowed_tos = allowed_tos    

    @handle("btnLogin", "click")
    def btnLogin_click(self, **event_args):
        print("loggin in...")
        print("allowed tos: ", self.allowed_tos)
        user_row = anvil.users.login_with_form()
        print(user_row)
    
        tos_accepted = anvil.server.call('has_accepted_tos', user_row['email'])
        if self.allowed_tos:
            tos_accepted = self.allowed_tos
    
        if not tos_accepted and tos_accepted is not None:
            self.lblErr.visible = True
            self.lblErr.text = "You cannot login unless you accept the TOS."
            open_form('frmTOS')
    
        if self.allowed_tos:
            self.btnLogin_click()
    
            if user_row is not None:
                username = user_row['Username']
                email = user_row['email']
    
                users = anvil.server.call('get_user_by_email', email)
                print(users)
    
                enabled = users['enabled']
    
                # this is here to mitigate an anvil bug (or feature idk)
                if not enabled:
                    print("User not enabled!")
                    self.lblErr.visible = True
                    self.lblErr.text = (
                        "This account has not been enabled by an admin! "
                        "A request has been sent."
                    )
                    return
    
                if username is None:
                    # assign new username
                    new_username = alert(frmUsername(), large=True, buttons=[])
    
                    shared_username = anvil.server.call(
                        'search_for_dupes',
                        new_username
                    )
    
                    print(new_username, shared_username)
    
                    impact = len(shared_username)
    
                    if impact > 0:
                        self.lblErr.visible = True
                        self.lblErr.text = "That username is taken. Sorry!"
                        return
    
                    if new_username:
                        anvil.server.call(
                            'add_username',
                            user_row,
                            new_username
                        )
                        username = new_username
                    else:
                        return
    
                open_form('frmMessaging', current_user=username)