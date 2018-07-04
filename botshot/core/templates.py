
class Templates:
    @staticmethod
    def message(message, next=None):
        def action(state):
            return message, next
        return action
    
    @staticmethod
    def input(entity, missing_message=None, accept_text=False, next=None):
        def action(state):
            if accept_text:
                state.dialog.context.set(entity, {"value":state.dialog.context.get('_message_text')})
            elif not state.dialog.context.get(entity, max_age=0):
                return missing_message, None
            return None, next
        return action

    @staticmethod
    def value_transition(entity, transitions, next=None):
        def action(state):
            value = state.dialog.context.get(entity)
            if value in transitions.keys():
                return None, transitions[value]
            return None, next
        return action

        