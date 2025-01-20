.. _security

Security
========
This page is for Torn and Tornium related security features that you are recommended to use.

.. note::
   If you have a security vulnerablity related to Tornium, please report this to tiksan [2383326] on Torn or Discord via a private/direct message. For more information, take a look at `Tornium's security policy <https://github.com/Tornium/tornium/blob/master/SECURITY.md>`_.

Torn Security
-------------
Since Tornium relies upon some of Torn's security procedures to keep it secure, it's recommended to make sure that you Torn account is secure while keeping your Tornium account secure.

API Key Security
^^^^^^^^^^^^^^^^
As most Torn-related websites use API keys for authentication, keeping your API keys secure and separate is recommended. Torn allows users to have up to 10 API keys with varying permissions, so typically it's best to use a separate API key per service and to give the service as little permissions as it needs (e.g. don't give a service that only needs public data a full access API key). Often, you can contact the developer of the service to determine what type of API key you'll need to use.

For information on your API key is used by Tornium, take a look at :ref:`this docs page<api_key_usage>`.

Faction API Security
^^^^^^^^^^^^^^^^^^^^
Faction-related API data is restricted to members with the API Access permission in-game. Additionally, many API tools (including Tornium) use faction AA as a permissions check to determine who has access to modify faction-related configs and view potentially sensitive information. As such, it is recommended to not have all roles have API Access.

Discord OAuth
^^^^^^^^^^^^^
Torn supports linking your Torn account with your Discord account through an OAuth process. However, this process is not 100% secure due to quirks with Torn's implementation of this. As such, be sure you aren't sharing URLs from this process or aren't signed into someone else's Discord account. 

Tornium Security
----------------
Tornium has additional security features on top of Torn's, but does rely upon the user and Torn to make sure that the platform remains secure.

Login Method
^^^^^^^^^^^^
Tornium supports both API key based login and Discord OAuth login. This allows users to not be required to have an API key on Tornium to access data when API calls are unnecessary by signing in with Discord.

Multi-Factor Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Tornium supports MFA with TOTP where the user needs to input a automatically refreshing code to finish the login process. This is recommended for use by faction leadership and server admins as Torn API keys can be misused by external parties.

Discord Login Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Tornium will send a notification through Discord to you if someone signs into your user account. This allows you to make sure that there isn't a malicious user signing into your account.

.. note::
   Tornium will also send a notification when an admin access your account for debugging/support.
