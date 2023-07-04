.. _ocnotifs:

Organized Crime Notifications
=============================
Tornium can send notifications for when organized crimes (OCs) are ready and/or delayed with optional pings to specified channel(s).

.. note::
    OC delays notifications are only sent for the first time the OC is delayed. Subsequent delays aren't notified by the bot, but subsequent readiness notifications are sent.

Notification Options
--------------------
For every faction that's been verified on the server, a ready channel, ready roles, delay channel, delay roles, and a initiation channel can be configured. This can be found on a sub-page accessed from the ``Organized Crimes`` section on the bot dashboard.

The ready and delay channels will be the channels to which OC ready and delay notifications will be sent respectively. The ready and delay roles are optional and will be pinged with the notifications if applicable. The initiation channel will be the channel to which notifications about the OC being initiated will be sent.

When an OC is delayed, buttons underneath the embed will state who is delaying the OC and the reason for the delay.