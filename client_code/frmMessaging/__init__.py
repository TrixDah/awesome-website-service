from ._anvil_designer import frmMessagingTemplate
from anvil import *
import anvil.server
from anvil.tables import app_tables
import time

msgCharLimit = 256

class frmMessaging(frmMessagingTemplate):
  def __init__(self, current_user, **properties):
    self.init_components(**properties)

    self.current_user = current_user
    self.current_chat = None 

    # Wait until the form is fully open on the screen before loading the data!
    self.set_event_handler('show', self.form_show)

    # initialize the dropdown
    self.drpNewUserSelect.items = anvil.server.call('get_usernames', self.current_user)

  def form_show(self, **event_args):
    # This runs the exact millisecond the form becomes visible
    self.show_chat_list_view()

  def show_chat_list_view(self):
    self.rpChatList.visible = True
    self.drpNewUserSelect.visible = True
    self.btnCreateChat.visible = True

    self.rpMessages.visible = False
    self.txtNewMessage.visible = False
    self.btnSend.visible = False
    self.btnSwitchChats.visible = False 

    self.rpChatList.items = anvil.server.call('get_user_chats', self.current_user)

  def show_messages_view(self):
    self.rpMessages.visible = True
    self.txtNewMessage.visible = True
    self.btnSend.visible = True
    self.btnSwitchChats.visible = True 

    self.rpChatList.visible = False
    self.drpNewUserSelect.visible = False
    self.btnCreateChat.visible = False

  def set_active_chat(self, chat_row):
    self.current_chat = chat_row

    participants = chat_row['Participants']
    display_name = chat_row['ChatName'] # Default fallback

    # Calculate the other person's name again for the header
    if len(participants) == 2:
      for person in participants:
        if person['Username'] != self.current_user:
          display_name = person['Username']

    self.lblWelcome.text = f"Chatting with: {display_name}"

    self.show_messages_view()
    self.refresh_messages()

  def refresh_messages(self):
    if self.current_chat:
      messages = anvil.server.call('get_chat_messages', self.current_chat)
      self.rpMessages.items = messages

      # Show/hide placeholder based on message count
      if len(messages) == 0:
        self.lblNoMessages.visible = True
        self.rpMessages.visible = False
      else:
        self.lblNoMessages.visible = False
        self.rpMessages.visible = True
  
  def btnSwitchChats_click(self, **event_args):
    self.current_chat = None
    self.show_chat_list_view()
 
  @handle('btnCreateChat', "click")
  def btnCreateChat_click(self, **event_args):
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
    new_message = self.txtNewMessage.text
    if new_message.strip() != "" and self.current_chat:
      if len(new_message) <= msgCharLimit:
        anvil.server.call('send_message', self.current_user, new_message, self.current_chat)
        self.txtNewMessage.text = "" 
        self.refresh_messages() 
      else:
        alert(f"Error: Message exceeds {msgCharLimit} character limit.")

  def btnLogout_click(self, **event_args):
    open_form('frmLogin')

  @handle("btnRefresh", "click")
  def btnRefresh_click(self, **event_args):
    time.sleep(1)
    if self.current_chat is not None:
      self.refresh_messages()
    else:
      self.rpChatList.items = anvil.server.call('get_user_chats', self.current_user)

  @handle("txtNewMessage", "pressed_enter")
  def txtNewMessage_pressed_enter(self, **event_args):
    """This method is called when the user presses Enter in this text box"""
    self.btnSend_click() # simulate a send button click

