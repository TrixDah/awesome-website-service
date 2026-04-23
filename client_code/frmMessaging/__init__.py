from ._anvil_designer import frmMessagingTemplate
from anvil import *
import anvil.server

class frmMessaging(frmMessagingTemplate):
  def __init__(self, current_user, **properties):
    self.init_components(**properties)

    self.current_user = current_user
    self.current_chat = None 

    self.show_chat_list_view()

  def show_chat_list_view(self):
    self.rpChatList.visible = True
    self.txtNewChatUser.visible = True
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
    self.txtNewChatUser.visible = False
    self.btnCreateChat.visible = False

  def set_active_chat(self, chat_row):
    self.current_chat = chat_row
    self.show_messages_view()
    self.refresh_messages()

  def refresh_messages(self):
    if self.current_chat:
      self.rpMessages.items = anvil.server.call('get_chat_messages', self.current_chat)

  
  def btnSwitchChats_click(self, **event_args):
    self.current_chat = None
    self.show_chat_list_view()
 
  @handle('btnCreateChat', "click")
  def btnCreateChat_click(self, **event_args):
    target = self.txtNewChatUser.text
    if target:
      new_chat = anvil.server.call('create_chat', self.current_user, target)
      if new_chat:
        self.txtNewChatUser.text = ""
        self.set_active_chat(new_chat)
      else:
        alert("User not found!")

  @handle("btnSend", "click")
  def btnSend_click(self, **event_args):
    new_message = self.txtNewMessage.text
    if new_message.strip() != "" and self.current_chat:
      anvil.server.call('send_message', self.current_user, new_message, self.current_chat)
      self.txtNewMessage.text = "" 
      self.refresh_messages()      

  def btnLogout_click(self, **event_args):
    open_form('frmLogin')

  @handle("btnRefresh", "click")
  def btnRefresh_click(self, **event_args):
    """This method is called when the button is clicked"""
    pass  # Write Code Here
