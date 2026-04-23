from ._anvil_designer import ItemTemplate2Template
from anvil import *

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    self.init_components(**properties)

  def lnkChatName_click(self, **event_args):
    get_open_form().set_active_chat(self.item)