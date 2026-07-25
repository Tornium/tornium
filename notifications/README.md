# Tornium Notification Examples
This directory contains the official notifications in a version-controlled format. Developers can also use this as examples for their own notifications.

For information on how to create your own notifications, see the [documentation](https://tornium.com/user/notifications/index.html).

Some notifications will include test cases using the same Lua VM as the production environment to validate notifications. These notifications' tests can be executed through the [notification_inator](https://github.com/Tornium/notification_inator/) project by providing the path to the directory for the notification:

```
❯ mix notification_inator.test ~/tornium/notifications/faction-traveling


13:15:46.186 [debug] ExUnit started
13:15:46.189 [debug] Attempting to load notification at .../tornium/notifications/faction-traveling
13:15:46.282 [info] Found and parsed notification "Faction Members Traveling"
Running ExUnit with seed: 359847, max_cases: 40

.
Finished in 0.09 seconds (0.00s async, 0.09s sync)
1 test, 0 failures
```
