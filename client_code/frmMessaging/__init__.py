from ._anvil_designer import frmMessagingTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.server
from anvil.tables import app_tables
import time
import datetime
from collections import OrderedDict

msgCharLimit = 256

MIN_POLL = 3
MAX_POLL = 13

class frmMessaging(frmMessagingTemplate):
    def __init__(self, current_user: str, **properties):
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
        self.drpNewUserSelect.items = anvil.server.call_s('get_usernames', self.current_user)

        # caching
        self.chat_cache = OrderedDict()
        self.cache_limit = 10

        self.chat_list_cache = {
            "data": None,
            "ver": None
        }
    
    def form_show(self, **event_args):
        # this runs the exact millisecond the form becomes visible
        self.show_chat_list_view()

    def _get_welcome_msg(self):
        try:
            chat: str | None = self.current_chat['ChatName']
            if len(self.current_chat['Participants']) == 2:
                chat = self._get_other_str(self.current_chat)
        except TypeError:
            chat: str | None = None
        return f"logged in as {self.current_user}.{(' chatting with' + ' ' + chat) if chat else ''}"

    def _get_other_str(self, chat_row):
        participants = chat_row['Participants'] or []
        if len(participants) != 2:
            raise Exception("GOSH! someone has called _get_other_str non-privatly or on a group chat")
        for person in participants:
            if person['Username'] != self.current_user:
                return person['Username']
        
        
    def show_chat_list_view(self):
        # this means that loading chats will take longer but it wont show the previous chats messages
        self.rpMessages.items = []
        self.cached_msgs = []
        self.cached_ver = None
        self.lblNoMessages.visible = False
        
        self.rpChatList.visible = True
        self.drpNewUserSelect.visible = True
        self.btnCreateChat.visible = True
    
        self.rpMessages.visible = False
        self.txtNewMessage.visible = False
        self.btnSend.visible = False
        self.btnSwitchChats.visible = False
        self.file_loader_1.visible = False
        self.lblWelcome.text = self._get_welcome_msg()

        cached = self._get_chats(force=False)
        self.rpChatList.items = cached
        self._refresh_chat_list()
    
    def show_messages_view(self):
        self.rpMessages.items = []
        self.cached_msgs = []
        self.cached_ver = None
        self.lblNoMessages.visible = False
        
        self.rpMessages.visible = True
        self.txtNewMessage.visible = True
        self.btnSend.visible = True
        self.btnSwitchChats.visible = True
        self.file_loader_1.visible = True

        self.rpChatList.visible = False
        self.rpChatList.items = None
        self.drpNewUserSelect.visible = False
        self.btnCreateChat.visible = False


    def _get_chats(self, force: bool = False):
        if not force and self.chat_list_cache["data"] is not None:
            return self.chat_list_cache["data"]

        chats = anvil.server.call_s('get_user_chats_data', self.current_user)
    
        self.chat_list_cache["data"] = chats
        return chats

    def _refresh_chat_list(self):
        chats = anvil.server.call_s('get_user_chats_data', self.current_user)

        old = self.chat_list_cache["data"]
    
        self.chat_list_cache["data"] = chats
        
        if chats != old:
            self.rpChatList.items = chats

    def set_active_chat(self, chat_row):
        self.current_chat = chat_row
        self.lblWelcome.text = self._get_welcome_msg()
    
        self.show_messages_view()
    
        cache = self._get_cache(chat_row)
    
        # 1. instant render from cache (no waiting)
        if cache["msgs"] is not None:
            self.rpMessages.items = cache["msgs"]
            self.lblNoMessages.visible = len(cache["msgs"]) == 0
            self.rpMessages.visible = len(cache["msgs"]) > 0
        else:
            # fallback placeholder load
            self.rpMessages.items = []
            self.lblNoMessages.visible = True
            self.rpMessages.visible = False
    
        anvil.server.call_s('mark_chat_read', self.current_chat, self.current_user)
    
        # 2. silent sync (does NOT block UI)
        self._sync_chat(self.current_chat)

    @handle("btnLogout", "click")
    def btnLogout_click(self, **event_args):
        """This method is called when the button is clicked"""
        anvil.users.logout()
        open_form('frmLogin')
        
    def refresh_messages(self, poll: bool = True):
        if not self.current_chat:
            return
    
        cache = self._get_cache(self.current_chat)

        if not poll:
            messages = anvil.server.call('get_chat_messages', self.current_chat)
    
            cache["msgs"] = messages
            cache["ver"] = None
    
            self.rpMessages.items = messages
    
            self.lblNoMessages.visible = len(messages) == 0
            self.rpMessages.visible = len(messages) > 0
            return
    
        # polling
        ver = anvil.server.call_s('get_chat_version', self.current_chat)
    
        if ver == cache["ver"]:
            self.pollingTimer.interval = min(
                self.pollingTimer.interval * 2,
                MAX_POLL
            )
            return
    
        # if there is a cache discrepancy, there is activity
        self.pollingTimer.interval = MIN_POLL
    
        messages = anvil.server.call_s('get_chat_messages', self.current_chat)
    
        cache["ver"] = ver
        cache["msgs"] = messages
    
        self.rpMessages.items = messages
        anvil.server.call_s('mark_chat_read', self.current_chat, self.current_user)
    
        self.lblNoMessages.visible = len(messages) == 0
        self.rpMessages.visible = len(messages) > 0

    def _sync_chat(self, chat):
        cache = self._get_cache(chat)

        # step 1: get version silently
        ver = anvil.server.call_s('get_chat_version', chat)
    
        if ver == cache["ver"]:
            return
    
        messages = anvil.server.call_s('get_chat_messages', chat)
    
        cache["ver"] = ver
        cache["msgs"] = messages
    
        if self.current_chat == chat:
            self.rpMessages.items = messages
            self.lblNoMessages.visible = len(messages) == 0
            self.rpMessages.visible = len(messages) > 0
    
            anvil.server.call_s('mark_chat_read', self.current_chat, self.current_user)
    
    @handle("btnSwitchChats", "click")
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
                    # pass the image_to_send to the server
                    result = anvil.server.call_s(
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
                        self.cached_ver = None
                        self.refresh_messages()
    
                finally:
                    self.btnSend.enabled = True
    
            else:
                alert(f"Error: Message exceeds {msgCharLimit} character limit.")
    
    @handle("txtNewMessage", "pressed_enter")
    def txtNewMessage_pressed_enter(self, **event_args):
        """This method is called when the user presses Enter in this text box"""
        self.btnSend_click()  # simulate a send button click

    @handle("pollingTimer", "tick")
    def _poll(self, **event_args):
        if not self.current_chat:
            return

        self._sync_chat(self.current_chat)

    def _get_cache(self, chat):
        """Ensure cache entry exists and mark as recently used"""
        if chat in self.chat_cache:
            self.chat_cache.move_to_end(chat)
            return self.chat_cache[chat]
    
        self.chat_cache[chat] = {"ver": None, "msgs": None}
    
        if len(self.chat_cache) > self.cache_limit:
            self.chat_cache.popitem(last=False)
    
        return self.chat_cache[chat]