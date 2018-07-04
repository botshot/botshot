from celery import shared_task


@shared_task
def on_message(uid, chat_id, message_text, dialog, from_user):
    from botshot.models import User, Chat, Message

    if chat_id is None:
        chat_id = uid
    user, was_created = User.objects.get_or_create(uid=uid, defaults={"uid": uid})
    if was_created:
        # TODO save user profile etc.
        user.save()
    chat, was_created = Chat.objects.get_or_create(chat_id=chat_id, defaults={"chat_id": chat_id, "user_uid": user})
    if was_created:
        chat.save()
    message = Message()
    message.chat = chat
    message.text = message_text
    message.is_from_user = from_user
    message.intent = dialog.context.get("intent", max_age=0)
    message.state = dialog.current_state_name
    message.save()
