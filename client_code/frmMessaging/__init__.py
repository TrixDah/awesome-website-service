from ._anvil_designer import frmMessagingTemplate
from anvil import *

class frmMessaging(frmMessagingTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
