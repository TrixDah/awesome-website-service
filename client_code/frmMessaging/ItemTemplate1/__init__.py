from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
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
    
    if not self.item['MessageText']:
      self.lblMessageText.visible = False
    else:
      self.lblMessageText.visible = True
      self.lblMessageText.text = self.item['MessageText']

    if db_time:
      melbourne_time = db_time.astimezone(anvil.tz.tzlocal())
      self.lblTime.text = melbourne_time.strftime("%b %d, %I:%M %p")

    # iMessage Alignment Logic
    current_user = get_open_form().current_user 

    if sender == current_user:
      self.lblMessageText.role = "bubble-me"
      self.lblMessageText.align = "right"
      self.lblSender.visible = False
      self.flow_panel_1.align = "right"
      self.image_1.align = "right"
      self.column_panel_2.role = "bubble-me-container"
    else:
      self.lblMessageText.role = "bubble-other"
      self.lblMessageText.align = "left"
      self.lblSender.visible = True
      self.image_1.align = "left"
      self.flow_panel_1.align = "left"
      self.column_panel_2.role = "bubble-other-container"
    
    readers = self.item['ReadBy'] or []
    # Remove the sender from the list so we only count OTHERS who read it
    other_readers = [r for r in readers if r['Username'] != self.item['Sender']]

    if len(other_readers) == 0:
      self.lnkStatus.text = "Delivered"
      self.lnkStatus.foreground = "gray"
    elif len(other_readers) == 1:
      self.lnkStatus.text = f"Read by {other_readers[0]['Username']}"
      self.lnkStatus.foreground = "blue"
    else:
      self.lnkStatus.text = f"Read by {len(other_readers)} people"
      self.lnkStatus.foreground = "blue"

  @handle("lnkStatus", "click")
  def lnkStatus_click(self, **event_args):
    readers = self.item['ReadBy'] or []
    other_readers = [r['Username'] for r in readers if r['Username'] != self.item['Sender']]

    if len(other_readers) > 1:
      # Join the names with commas and show them in a popup
      names_list = "\n".join(other_readers)
      alert(names_list, title="Read by:")

