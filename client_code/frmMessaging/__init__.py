from ._anvil_designer import frmMessagingTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.server
from anvil.tables import app_tables
import time
import datetime

# Configuration Constants
MSG_CHAR_LIMIT = 256
CLICK_THROTTLE_SECONDS = 2
SEND_THROTTLE_SECONDS = 1
REFRESH_THROTTLE_SECONDS = 2

class frmMessaging(frmMessagingTemplate):
  def __init__(self, current_user, **properties):
    self.init_components(**properties)

    self.current_user = current_user
    self.current_chat = None 
    self.last_refresh_time = datetime.datetime.now() - datetime.timedelta(seconds=30)
    self.last_send_time = 0
    self.last_click_time = datetime.datetime.now()

    # Wait until the form is fully open on the screen before loading the data!
    self.set_event_handler('show', self.form_show)

    # initialize the dropdown
    self.drpNewUserSelect.items = anvil.server.call('get_usernames', self.current_user)

  def _set_visibility(self, visible_components, hidden_components):
    """Helper: Bulk set component visibility."""
    for component in visible_components:
      component.visible = True
    for component in hidden_components:
      component.visible = False

  def _get_display_name(self, chat_row):
    """Helper: Determine display name for a chat."""
    display_name = chat_row['ChatName']
    participants = chat_row['Participants'] or []
    
    # For DMs with 2 people, show the other person's name
    if not display_name and len(participants) == 2:
      for person in participants:
        if person['Username'] != self.current_user:
          return person['Username']
    
    return display_name or "Direct Message"

  def form_show(self, **event_args):
    """Form becomes visible."""
    self.show_chat_list_view()

  def show_chat_list_view(self):
    """Display chat list and hide message view."""
    self._set_visibility(
      [self.rpChatList, self.drpNewUserSelect, self.btnCreateChat],
      [self.rpMessages, self.txtNewMessage, self.btnSend, self.btnSwitchChats, self.file_loader_1, self.btnRefresh]
    )
    self.rpChatList.items = anvil.server.call('get_user_chats_data', self.current_user)
    
  def show_messages_view(self):
    """Display message view and hide chat list."""
    self._set_visibility(
      [self.rpMessages, self.txtNewMessage, self.btnSend, self.btnSwitchChats, self.file_loader_1, self.btnRefresh],
      [self.rpChatList, self.drpNewUserSelect, self.btnCreateChat]
    )

  def set_active_chat(self, chat_row):
    """Set the current chat and display its messages."""
    self.current_chat = chat_row
    self.lblWelcome.text = f"Chatting with: {self._get_display_name(chat_row)}"
    
    self.show_messages_view()
    anvil.server.call('mark_chat_read', self.current_chat, self.current_user)
    self.refresh_messages()

  def refresh_messages(self):
    """Refresh messages and update placeholder visibility."""
    if self.current_chat:
      messages = anvil.server.call('get_chat_messages', self.current_chat)
      self.rpMessages.items = messages
      
      has_messages = len(messages) > 0
      self.lblNoMessages.visible = not has_messages
      self.rpMessages.visible = has_messages

  def _throttle_action(self, throttle_time, last_time_attr):
    """Helper: Check if enough time has passed for throttled action."""
    now = datetime.datetime.now()
    if (now - getattr(self, last_time_attr)).total_seconds() < throttle_time:
      return False
    setattr(self, last_time_attr, now)
    return True

  def btnSwitchChats_click(self, **event_args):
    """Switch back to chat list view."""
    if self._throttle_action(CLICK_THROTTLE_SECONDS, 'last_click_time'):
      self.current_chat = None
      self.show_chat_list_view()
  
  @handle('btnCreateChat', "click")
  def btnCreateChat_click(self, **event_args):
    """Create a new chat with selected user."""
    target = self.drpNewUserSelect.selected_value
    if target:
      new_chat = anvil.server.call('create_chat', self.current_user, target)
      if new_chat:
        self.drpNewUserSelect.selected_value = None
        self.set_active_chat(new_chat)
      else:
        alert("User not found!")

  @handle("btnSend", "click")
  def btnSend_click(self, **event_args):
    """Send a message or image."""
    if not self._throttle_action(SEND_THROTTLE_SECONDS, 'last_send_time'):
      return 

    new_message = self.txtNewMessage.text
    image_to_send = self.file_loader_1.file

    # Check if there is EITHER text OR an image to send
    if (new_message.strip() or image_to_send) and self.current_chat:
      if len(new_message) <= MSG_CHAR_LIMIT:
        self.btnSend.enabled = False

        try:
          result = anvil.server.call('send_message', self.current_user, new_message, self.current_chat, image_to_send)

          if not result["success"]:
            alert(result["error"]) 
          else:
            self.txtNewMessage.text = "" 
            self.file_loader_1.clear()
            self.refresh_messages() 

        finally:
          self.btnSend.enabled = True

      else:
        alert(f"Error: Message exceeds {MSG_CHAR_LIMIT} character limit.")

  @handle("txtNewMessage", "pressed_enter")
  def txtNewMessage_pressed_enter(self, **event_args):
    """Send message when user presses Enter."""
    self.btnSend_click()

  @handle("btnLogout", "click") 
  def btnLogout_click(self, **event_args):
    """Logout and return to login form."""
    anvil.users.logout()
    open_form('frmLogin')

  @handle("btnRefresh", "click")
  def btnRefresh_click(self, **event_args):
    """Refresh messages with throttling."""
    if self._throttle_action(REFRESH_THROTTLE_SECONDS, 'last_refresh_time'):
      self.refresh_messages()
