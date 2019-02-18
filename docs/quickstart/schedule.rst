###################
Scheduling messages
###################

You can use the MessageScheduler API to schedule messages.

---------------------
Adding a schedule
---------------------

You can use a schedule to send a message to a group of users at a specific time in the future.

.. code-block:: python

    scheduler = MessageScheduler()
    payload = {"_state": "default.root"}
    user_spec = {"conversation_ids": [1, 2, 3]}
    at = timezone.now() + timedelta(minutes=5)
    
    scheduler.add_schedule(action=payload, user_spec=user_spec, at=at)

---------------------------
Adding a recurrent schedule
---------------------------

To send the message periodically, you can add a recurrent schedule.

.. code-block:: python

    scheduler = MessageScheduler()
    payload = {"_state": "default.root"}
    user_spec = {"conversation_ids": [1, 2, 3]}

    scheduler.add_recurrent_schedule(
        action=payload, user_spec=user_spec, 
        hour=12, minute=00, 
        weekday=1
    )
