from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.users
from anvil import get_open_form
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil
import datetime
import anvil.tz 

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    self.init_components(**properties)

    sender = self.item['Sender']
    db_time = self.item['TimeSent']

    self.lblMessageText.text = self.item['MessageText']
    self.lblSender.text = sender

    # Handle image visibility and alignment
    if self.item['MessageImage'] is None:
      self.image_1.visible = False
    else:
      self.image_1.visible = True
      # Set max height for responsive image sizing
      self.image_1.height = 200  # adjust as needed

    if db_time:
      melbourne_time = db_time.astimezone(anvil.tz.tzlocal())
      self.lblTime.text = melbourne_time.strftime("%b %d, %I:%M %p")

    # iMessage Alignment Logic
    current_user = get_open_form().current_user 

    if sender == current_user:
      self.lblMessageText.role = "bubble-me"
      self.lblMessageText.align = "right"
      self.lblTime.align = "right"
      self.lblSender.visible = False
      self.image_1.align = "right"
      self.column_panel_2.role = "bubble-me-container"
    else:
      self.lblMessageText.role = "bubble-other"
      self.lblMessageText.align = "left"
      self.lblTime.align = "left"
      self.lblSender.visible = True
      self.image_1.align = "left"
      self.column_panel_2.role = "bubble-other-container"


