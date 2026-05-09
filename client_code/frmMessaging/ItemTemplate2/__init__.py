from ._anvil_designer import ItemTemplate2Template
from anvil import *

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    self.init_components(**properties)

  def _get_display_name(self):
    """Get display name for chat (other user's name for DMs or chat name)."""
    current_user = get_open_form().current_user
    display_name = self.item['chat_name']
    participants = self.item['chat_row']['Participants']

    # For 1-on-1 DMs, show the OTHER person's name
    if len(participants) == 2:
      for person in participants:
        if person['Username'] != current_user:
          return person['Username']

    return display_name

  def refresh_data_bindings(self, **event_args):
    """Refresh when chat list data updates."""
    self.lnkChatName.text = self._get_display_name()

    # Show unread badge if messages are unread
    unread_count = self.item.get('unread_count', 0)
    if unread_count > 0:
      self.lblUnread.text = f"({unread_count} New)"
      self.lblUnread.visible = True
    else:
      self.lblUnread.visible = False

  def lnkChatName_click(self, **event_args):
    """Open chat when clicked."""
    get_open_form().set_active_chat(self.item['chat_row'])
