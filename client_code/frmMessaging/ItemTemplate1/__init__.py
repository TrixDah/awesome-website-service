from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil
import datetime
import anvil.tz 

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Now we manually format the time using Python!
    # We check if there is a time saved to avoid errors on empty rows
    if self.item['TimeSent']:
      # 1. Grab the time from the database
      db_time = self.item['TimeSent']
      # 2. Convert it to Melbourne time
      melbourne_time = db_time.astimezone(anvil.tz.tzlocal())
      # 3. Format it and set it to the label
      self.lblTime.text = melbourne_time.strftime("%b %d, %I:%M %p")

    # Any code you write here will run before the form opens.
