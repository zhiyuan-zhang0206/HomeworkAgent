import time
from wxauto import WeChat
from loguru import logger
from langchain_core.tools import tool
class WeChatManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(WeChatManager, cls).__new__(cls)
            logger.info("Creating new WeChatAgent instance")
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            logger.info("Initializing WeChatAgent")
            self.wx = WeChat()
            # Dictionary to store messages for each contact
            self.contact_messages = {}
            self.initialized = True
            logger.success("WeChatAgent initialized successfully")

    def _init_contact_messages(self, contact):
        """Initialize message history for a new contact.

        Args:
            contact (str): The contact name to initialize messages for.
        """
        logger.info(f"Initializing message history for contact: {contact}")
        all_msgs = self._get_all_messages(contact)
        self.contact_messages[contact] = {
            'messages': all_msgs,
            'last_retrieved_id': all_msgs[-1]["id"] if all_msgs else None
        }
        logger.info(f"Initial message count for {contact}: {len(all_msgs)}")

    def _get_all_messages(self, contact):
        logger.info("Getting all messages")
        self.wx.ChatWith(contact)
        all_msgs = self.wx.GetAllMessage(savepic=False)
        all_msgs = [{"content": msg.content, 
                     "sender": msg.sender, 
                     "type": msg.type,
                     "id": msg.id} for msg in all_msgs]
        logger.info(f"All messages: {len(all_msgs)} messages")
        return all_msgs

    def _update_messages(self, contact):
        logger.info(f"Updating messages for contact: {contact}")
        # Initialize contact messages if not exists
        if contact not in self.contact_messages:
            self._init_contact_messages(contact)
            return []  # Return empty list since we just initialized

        all_msgs = self._get_all_messages(contact)
        new_msgs = []
        last_id = self.contact_messages[contact]['last_retrieved_id']
        
        for msg in reversed(all_msgs):
            if msg["id"] != last_id:
                new_msgs.append(msg)
                logger.debug(f"Added new message: {msg}")
            else:
                break
                
        new_msgs = list(reversed(new_msgs))
        logger.info(f"New message count: {len(new_msgs)}. Total messages count: {len(self.contact_messages[contact]['messages'])}")
        
        self.contact_messages[contact]['messages'].extend(new_msgs)
        if new_msgs:  # Update last retrieved ID only if we got new messages
            self.contact_messages[contact]['last_retrieved_id'] = new_msgs[-1]["id"]
            
        return new_msgs
        
    def get_all_new_messages(self):
        """Gets all new messages from all contacts.

        Returns:
            dict: A dictionary where keys are contact names and values are lists of message dictionaries.
        """
        logger.info("Getting all new messages")
        all_new_messages = self.wx.GetAllNewMessage()
        result = {}
        for contact, messages in all_new_messages.items():
            result[contact] = [{"sender": msg.sender, 
                              "content": msg.content,
                              "type": msg.type} for msg in messages]
        return result

    def send_msg(self, contact, message):
        logger.info(f"Sending message to {contact}: {message}")
        self.wx.SendMsg(message, contact)
        logger.success("Message sent successfully")

    def get_new_messages(self, contact):
        logger.info(f"Getting new messages for contact: {contact}")
        return self._update_messages(contact)
    
    def get_new_replies(self, contact):
        new_messages = self._update_messages(contact)
        replies = [{"sender": msg["sender"], "content": msg["content"]} for msg in new_messages if msg["type"] == "friend"]
        return replies

@tool
def get_all_new_messages() -> str:
    """Gets all new messages from all contacts.

    Returns:
        str: A string representation of a dictionary containing new messages from all contacts.
    """
    manager = WeChatManager()
    messages = manager.get_all_new_messages()
    return str(messages)

@tool
def send_message(message: str, contact: str, wait_for_reply: int = 600):
    """Sends a message to the WeChat contact (or group chat) and waits for replies.

    Args:
        message (str): The message to send to the group chat.
        contact (str): The contact or group to send the message to.
        wait_for_reply (int, optional): Maximum time to wait for replies in seconds.
            Defaults to 10 minutes.

    Returns:
        str: If replies are received, returns a string representation of a list containing
            all reply message contents. If no replies are received within the timeout period,
            returns a timeout message.
    """
    manager = WeChatManager()
    manager.send_msg(contact, message)
    
    if wait_for_reply <= 0:
        return "Message sent successfully (not waiting for replies)"
    
    start_time = time.time()
    while True:
        all_messages = manager.get_all_new_messages()
        if contact in all_messages:
            messages = all_messages[contact]
            # filter out messages that are not replies
            messages = [msg for msg in messages if msg["type"] == "friend"]
            if messages:  # If we have messages from this contact
                return '\n'.join([f'Contact {contact} replied: {msg["content"]}' for msg in messages])
        
        if time.time() - start_time > wait_for_reply:
            timeout_msg = f"No new messages received from {contact} after {wait_for_reply} seconds"
            logger.warning(timeout_msg)
            return timeout_msg
            
        time.sleep(3)

__all__ = ["send_message", "get_all_new_messages"]