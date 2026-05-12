from ._anvil_designer import frmTOSTemplate
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import alert
import anvil.js

class frmTOS(frmTOSTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)

        anvil.js.window.accept_tos = self.accept_tos
        anvil.js.window.decline_tos = self.decline_tos

    def accept_tos(self):
        anvil.open_form('frmLogin', True)

    def decline_tos(self):
        anvil.open_form('frmLogin', False)