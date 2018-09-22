from botshot.core.parsing.raw_message import RawMessage
from botshot.models import ChatSession, ChatUser, ChatMessage
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class MessageManager:

    def process(self, raw_message: RawMessage):
        entities = raw_message.payload
        # TODO entities.update(self.parse_text(raw_message.text))

        message = ChatMessage()
        message.type = raw_message.type
        message.text = raw_message.text
        message.is_user = True
        message.set_entities(entities)

        with transaction.atomic():
            try:
                session: ChatSession = ChatSession.objects.select_for_update().get(
                    interface_name=raw_message.interface.name,
                    raw_session_id=raw_message.raw_session_id
                )
            except ObjectDoesNotExist:
                session = ChatSession()
                session.interface_name = raw_message.interface.name
                session.raw_session_id = raw_message.raw_session_id
                session.set_meta(raw_message.session_meta)
                raw_message.interface.fill_session_details(session)

            session.last_message_time = timezone.now()

            message.sender = ChatUser.objects.get_or_create(user_id=user_id, defaults={
                'session': session,
                'meta': raw_message.user_meta
            })

            # dialog manager is constructed directly with message
            dialog = DialogManager(FLOWS, message)
            dialog.run()

            # should propagate to save sender, session and context
            # messages will be saved at all times and possibly erased after a time period or using max total messages limit
            message.save()