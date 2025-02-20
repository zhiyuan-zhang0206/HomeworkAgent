import time
from loguru import logger
from fastapi import HTTPException
from loguru import logger
from langchain_core.tools import tool
import win32com.client as win32
import pythoncom
import os
from ..config import USER_EMAIL, EMAIL_DRAFT_MODE

@tool
def send_email_to_user(message: str, wait_response: bool = False, timeout_minutes: int = 10)->str:
    '''
    Send an email message to the user. A convenient tool for `send_email` with the user's email hardcoded in the config.
    
    Args:
        - message: str
            The message to send to the user.
        - wait_response: bool
            Whether to wait for the user's response.
        - timeout_minutes: int
            The timeout in minutes for waiting for the user's response.
    '''
    message = send_email.invoke({"to": USER_EMAIL, "subject": "Message from Agent", "body": message})
    if not wait_response:
        return message
    start_time = time.time()
    while time.time() - start_time < timeout_minutes * 60:
        latest_email = get_latest_email.invoke({})
        if latest_email['unread']:
            return message + f"\nGot response: {latest_email}"
        time.sleep(3)
    return message + f"\nNo response from user in {timeout_minutes} minutes."


@tool
def send_email(to:str, subject:str, body:str)->None:
    '''
    Send an email.

    Args:
        - to: str
            The email address to send to.
        - subject: str
            The subject of the email.
        - body: str
            The body of the email.
    '''
    try:
        pythoncom.CoInitialize()
        
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        
        if EMAIL_DRAFT_MODE:
            mail.Save()
            logger.info(f"Email saved as draft \nto: {to}\nwith subject: {subject}\nand body: {body}")
            message = "Email sent." # testing purposes
        else:
            logger.info(f"Sending email \nto: {to}\nwith subject: {subject}\nand body: {body}")
            mail.Send()
            logger.info(f"Email sent successfully to {to}")
            message = "Email sent."

    except Exception as e:
        message = f"Failed to {'save' if EMAIL_DRAFT_MODE else 'send'} email: {str(e)}"
        logger.error(message)
    finally:
        pythoncom.CoUninitialize()
    return message

@tool
def get_latest_email():
    '''
    Retrieves the latest email from the inbox.
    '''
    logger.info("Getting latest email")
    start_time = time.time()
    try:
        pythoncom.CoInitialize()
        outlook = win32.Dispatch('outlook.application')
        namespace = outlook.GetNamespace("MAPI")
        inbox = namespace.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)
        
        
        message = messages[0]
        try:
            # Capture original unread state first
            original_unread = bool(message.UnRead)
            
            # Mark as read if unread
            if original_unread:
                message.UnRead = False
                message.Save()
            
            # Get sender information
            sender = message.SenderName
            if not sender:
                sender = message.Sender.Address if message.Sender else "Unknown Sender"
            
            email_data = {
                "subject": message.Subject or "",
                "sender": sender,
                "received_time": str(message.ReceivedTime) if message.ReceivedTime else "",
                "body": message.Body or "",
                "unread": original_unread
            }
        except Exception as msg_error:
            logger.warning(f"Error processing message: {str(msg_error)}")

        logger.info(f"Processed latest email in {time.time() - start_time} seconds")
        return email_data
        
    except Exception as e:
        error_msg = f"Failed to fetch email: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        pythoncom.CoUninitialize()


__all__ = ['send_email_to_user', 
           'send_email',
           'get_latest_email'
           ]