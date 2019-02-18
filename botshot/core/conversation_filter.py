from abc import ABC, abstractmethod
from botshot.core.persistence import DictSerializable
from botshot.core.context import Context
from botshot.models import ChatConversation


class ConversationFilter(DictSerializable, ABC):
    """
    A filter representing a set of conversations.
    """

    @abstractmethod
    def get_ids(self) -> list:
        """Returns the IDs of all conversations matching this filter."""
        pass


class ListConversationFilter(ConversationFilter):

    def __init__(self, ids: list):
        super().__init__()
        self.ids = ids

    def get_ids(self):
        return self.ids


class AllConversationFilter(ConversationFilter):

    def get_ids(self):
        return [c.id for c in ChatConversation.objects.all()]


class ContextConversationFilter(ConversationFilter):

    def get_ids(self):
        matching = []
        for conversation in ChatConversation.objects.all():
            context = Context.from_dict(dialog=None, data=conversation.context_dict)
            if self._filter_context(context):
                matching.append(conversation.id)
        return matching
    
    @abstractmethod
    def _filter_context(self, context) -> bool:
        """
        Returns true iff a context is matching the filter.
        Override this method in your implementation.
        """
        pass


class EntityValueConversationFilter(ContextConversationFilter):
    
    def __init__(self, entity, value=None, max_age=None):
        super().__init__()
        self.entity = entity
        self.value = value
        self.max_age = max_age

    def _filter_context(self, context):
        val = context.get_value(self.entity, max_age=self.max_age)
        # No specific value requested, accept any value
        if self.value is None:
            return bool(val)
        return val == self.value
