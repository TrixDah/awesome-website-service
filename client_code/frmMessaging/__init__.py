from ._anvil_designer import frmMessagingTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.server
from anvil.tables import app_tables
import time
import datetime

msgCharLimit = 256

class frmMessaging(frmMessagingTemplate):
    def __init__(self, current_user, **properties):
        self.init_components(**properties)
    
        self.current_user = current_user
        self.current_chat = None
        self.last_refresh_time = datetime.datetime.now() - datetime.timedelta(seconds=30)
        self.last_send_time = 0
        self.last_click_time = datetime.datetime.now()
    
        self.lblWelcome.text = f"logged in as {self.current_user}.{(' chatting with' + self.current_chat) if self.current_chat else ''}"
    
        # Wait until the form is fully open on the screen before loading the data!
        self.set_event_handler('show', self.form_show)
    
        # initialize the dropdown
        self.drpNewUserSelect.items = anvil.server.call('get_usernames', self.current_user)
    
    def form_show(self, **event_args):
        # this runs the exact millisecond the form becomes visible
        self.show_chat_list_view()

    def _get_welcome_msg(self):
        try:
            chat: str | None = self.current_chat['ChatName']
            if len(self.current_chat['Participants']) == 2:
                chat = self._get_other_other_str(self.current_chat)
        except TypeError:
            chat: str | None = None
        return f"logged in as {self.current_user}.{(' chatting with' + ' ' + chat) if chat else ''}"

    def _get_other_other_str(self, chat_row):
        participants = chat_row['Participants'] or []
        if len(participants) != 2:
            raise Exception("GOSH! someone has called _get_other_other_str non-privatly or on a group chat")
        for person in participants:
            if person['Username'] != self.current_user:
                return person['Username']
        
        
    def show_chat_list_view(self):
        self.rpChatList.visible = True
        self.drpNewUserSelect.visible = True
        self.btnCreateChat.visible = True
    
        self.rpMessages.visible = False
        self.txtNewMessage.visible = False
        self.btnSend.visible = False
        self.btnSwitchChats.visible = False
        self.file_loader_1.visible = False
        self.btnRefresh.visible = False
        self.rpChatList.items = anvil.server.call('get_user_chats_data', self.current_user)
        self.lblWelcome.text = self._get_welcome_msg()
    
    def show_messages_view(self):
        self.rpMessages.visible = True
        self.txtNewMessage.visible = True
        self.btnSend.visible = True
        self.btnSwitchChats.visible = True
        self.file_loader_1.visible = True
        self.btnRefresh.visible = True

        self.rpChatList.visible = False
        self.drpNewUserSelect.visible = False
        self.btnCreateChat.visible = False

        
    
    def set_active_chat(self, chat_row):
        self.current_chat = chat_row
        self.lblWelcome.text = self._get_welcome_msg()
    
        # 1. Grab the default name and participants directly from the database row
        display_name = chat_row['ChatName']
        participants = chat_row['Participants'] or []
    
        # 2. If it's a DM (no formal ChatName set) and has exactly 2 people, find the other person's name
        if len(participants) == 2:
            display_name = self._get_other_other_str(chat_row)
    
            # 3. Fallback just in case
        if not display_name:
            display_name = "Direct Message"
    
        self.show_messages_view()
    
        anvil.server.call('mark_chat_read', self.current_chat, self.current_user)
    
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
        now = datetime.datetime.now()
    
        # Check if 0.5 seconds have passed
        if (now - self.last_click_time).total_seconds() < 2:
            return
    
        self.last_click_time = now
        self.current_chat = None
        self.show_chat_list_view()
    
        self.last_click_time = now
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
        current_time = time.time()
    
        if current_time - self.last_send_time < 1:
            return
    
        self.last_send_time = current_time
    
        new_message = self.txtNewMessage.text
        image_to_send = self.file_loader_1.file  # Grab the image
    
        # Check if there is EITHER text OR an image to send
        if (new_message.strip() != "" or image_to_send is not None) and self.current_chat:
            if len(new_message) <= msgCharLimit:
                self.btnSend.enabled = False
    
                try:
                    # Pass the image_to_send to the server
                    result = anvil.server.call(
                        'send_message',
                        self.current_user,
                        new_message,
                        self.current_chat,
                        image_to_send
                    )
    
                    if not result["success"]:
                        alert(result["error"])
                    else:
                        self.txtNewMessage.text = ""
                        self.file_loader_1.clear()  # Clear the image upload so it's ready for the next one!
                        self.refresh_messages()
    
                finally:
                    self.btnSend.enabled = True
    
            else:
                alert(f"Error: Message exceeds {msgCharLimit} character limit.")
    
    @handle("txtNewMessage", "pressed_enter")
    def txtNewMessage_pressed_enter(self, **event_args):
        """This method is called when the user presses Enter in this text box"""
        self.btnSend_click()  # simulate a send button click
    
    @handle("btnLogout", "click")
    def btnLogout_click(self, **event_args):
        anvil.users.logout()
        open_form('frmLogin')
    
    @handle("btnRefresh", "click")
    def btnRefresh_click(self, **event_args):
        now = datetime.datetime.now()
    
        # Throttle: Only allow refresh if it's been more than 2 seconds
        if (now - self.last_refresh_time).total_seconds() < 2:
            # Optional: Notification to tell the user to slow down
            # n = Notification("Refreshing too fast! Please wait a moment.", timeout=2)
            # n.show()
            return
    
            # Update the timestamp and run the refresh
        self.last_refresh_time = now
        self.refresh_messages()