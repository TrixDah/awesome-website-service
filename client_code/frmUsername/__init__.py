from ._anvil_designer import frmUsernameTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class frmUsername(frmUsernameTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  @handle("save_button", "click")
  def save_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    username = self.username_box.text

    if not username:
      alert("Pick a username!")
      return

    self.raise_event("x-close-alert", value=username)
