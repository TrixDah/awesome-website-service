from ._anvil_designer import ItemTemplate2Template
from anvil import *

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    self.init_components(**properties)

    current_user = get_open_form().current_user
    participants = self.item['Participants']
    display_name = self.item['ChatName'] # Default fallback

    # If it is a 1-on-1 DM, find the OTHER person's name
    # If it is a 1-on-1 DM (and NOT the General Chat), find the OTHER person's name
    if len(participants) == 2 and self.item['ChatName'] != "General Chat":
      for person in participants:
        if person['Username'] != current_user:
          display_name = person['Username']

    # Manually bind the dynamic name to the link
    self.lnkChatName.text = display_name

  def lnkChatName_click(self, **event_args):
    get_open_form().set_active_chat(self.item)