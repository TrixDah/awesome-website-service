from ._anvil_designer import frmMessagingTemplate
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from anvil import open_form
from anvil import *

class frmMessaging(frmMessagingTemplate):
  def __init__(self, current_user, **properties):
    self.init_components(**properties)

    # Save the passed username and set up the UI
    self.current_user = current_user
    self.refresh_messages()

  def refresh_messages(self):
    """Helper function to fetch and bind messages"""
    self.rpMessages.items = anvil.server.call('get_messages')

  # Bind the refresh button
  @handle("btnRefresh", "click")
  def refresh_chat(self, **event_args):
    self.refresh_messages()

  # Bind the send button
  @handle("btnSend", "click")
  def send_new_message(self, **event_args):
    new_message = self.txtNewMessage.text

    if new_message.strip() != "":
      anvil.server.call('send_message', self.current_user, new_message)
      self.txtNewMessage.text = "" 
      self.refresh_messages()      

  # Bind the logout button
  @handle("btnLogout", "click")
  def perform_logout(self, **event_args):
    open_form('frmLogin')