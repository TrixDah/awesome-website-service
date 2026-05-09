from ._anvil_designer import ItemTemplate2Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    # Keep this, but nothing else goes in __init__!
    self.init_components(**properties)

  def refresh_data_bindings(self, **event_args):
    """This function automatically runs whenever the chat list data is updated."""
    current_user = get_open_form().current_user
    display_name = self.item['chat_name'] 
    participants = self.item['chat_row']['Participants']

    # If it is a 1-on-1 DM, find the OTHER person's name
    if len(participants) == 2:
      for person in participants:
        if person['Username'] != current_user:
          display_name = person['Username']

    # Bind the dynamic name to the link
    self.lnkChatName.text = display_name

    # --- UNREAD BADGE LOGIC ---
    # Check if there are unread messages
    if self.item.get('unread_count', 0) > 0:
      self.lblUnread.text = f"({self.item['unread_count']} New)"
      self.lblUnread.visible = True
    else:
      self.lblUnread.visible = False

  def lnkChatName_click(self, **event_args):
    get_open_form().set_active_chat(self.item['chat_row'])