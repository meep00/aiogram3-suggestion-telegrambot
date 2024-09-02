import os

# Bot Data
TOKEN = os.getenv("TOKEN")

# Admin Chat
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

DATABASE_URL = os.getenv("DATABASE_URL")

CHANNEL_ID = os.getenv("CHANNEL_ID")

THROTTLE_TIME = int(os.getenv("THROTTLE_TIME"))

MESSAGE_LIFETIME_HOURS = int(os.getenv("MESSAGE_LIFETIME_HOURS"))
MESSAGE_LIFETIME_SECONDS = int(os.getenv("MESSAGE_LIFETIME_SECONDS"))

TEXT_MESSAGES = {
    'start': 'Welcome to Suggestions Bot 👋 \n\nPlease, send your message and we will process your request.',
    'message_template': '<i>Message from: <b>@{0}</b>.</i>\n\n{1}<b>id: {2}</b>',
    'is_banned': '❌ User is banned!',
    'has_banned': '✅ User has been successfully banned!',
    'already_banned': '❌ User is already banned!',
    'has_unbanned': '✅ User has been successfully un-banned!',
    'user_banned': '🚫 You cannot send messages to this bot!',
    'pending': 'Thank you for your suggestion! The admin received it',
    'unsupported_format': '❌ Format of your message is not supported and it will not be forwarded.',
    'rm': '❌ Clear chat',
    'banlist': '👨‍🦽 Banlist',
    'help': '/help',
    'choose': '😊Choose what to do with this shit',
    'close': '❌Close',
    'user_is_not_registered': '❌ This user is not registered in the database',
    'no_args': '❌Error: argument was not passed',
    'failed_unban': '❌Error: Failed to unban the user',
    'list_of_banned': '👨‍🦽The list of banned users',
    'to_unblock_enter': "To unblock a user, write the /unblock command to the bot and the user's ID.\n"
                        'For example: /unblock 123456789',
    'invalid_args': '❌Error: Invalid user ID format.',
    'failed_ban': '❌Ban failed',
    'edit_text': 'Please, enter the new caption',
    'album_limit': '❌You can send up to three photos',
    'admin_start': 'Welcome, admin 👋',
    'posted': '✅Posted',
    'cleared': '✅The chat has been cleared',
    'not_cleared': '❌The chat or db has not been cleared, please contact technical support',
    'throttling': '❌You can\'t send an offer yet, try again later\n(the delay from the previous suggestion is 5 minutes)',
    'echo': '❌ I don\'t understand you'
}

LINK = os.getenv("LINK")
LINK_TEXT = os.getenv("LINK_TEXT")
