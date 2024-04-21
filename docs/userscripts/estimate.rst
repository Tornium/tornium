.. _estimate_userscript:

Estimate Userscript
===================
The estimation userscript is a free alternative to other services (such as BSP) using data from Tornium.

.. warning::
   This userscript is in active development, so the userscript's features listed here may change in the near future. This documentation was last updated for v0.3.3.

Screenshots
-----------
.. image:: /_static/images/profile_estimate.png
    :alt: Example user profile estimates

.. image:: /_static/images/attack_loader_estimate.png
    :alt: Example user attack loader estimates

Installation Instruction
------------------------
This userscript is currently tested on Firefox and Chrome using ViolentMonkey and TamperMonkey. Additionally, TornPDA has limited support, but should work to at least a limited degree.

#. If you don't have one already, install a userscript manager on your browser. This does not apply to TornDPA.
#. Navigate to the `userscript <https://github.com/Tornium/tornium-core/blob/master/static/userscripts/tornium-estimate.user.js>`_ and press the raw button (or visit `this <https://github.com/Tornium/tornium-core/blob/master/static/userscripts/tornium-estimate.user.js>`_). If your userscript manager is installed properly, this will automatically install the userscript and show a confirmation page from the userscript manager.
#. Visit a `user profile <https://www.torn.com/profiles.php?XID=2383326>`_ on Torn which will show a button under the username to authenticate the userscript. Pressing the button will send you to Tornium's OAuth portal if you're already signed in. If you're not already signed in, you can sign in with the Discord sign-in (so you don't need to provide an API key) or with a `limited access API key <https://www.torn.com/preferences.php#tab=api?&step=addNewKey&title=Tornium&type=3>`_. Once signed in, you can authorize the application to do perform actions against your Tornium account, and you'll be redirected back to Torn (eventually).
#. Now you can visit any page the userscript supports to see stats according to Tornium.

.. note ::
   Due to security with how userscripts work, to help prevent malicious use of data, you will be forced to re-authourize the userscript once a week.

How It Works
------------
Depending on the page, the userscript will make an API call to Tornium's servers to retrieve an estimate of the user's stats or to retrieve the users stats from its database. An uncapped fair fight score will also be generated from your stats the last time you've visited the gym page. Being uncapped, this allows you to quickly see the relative strength of the target with 3x FF being about 50-75% of your stats.

Supported Pages
---------------
#. User profile: shows exact estimate and value from stat database with FFs
#. Attack loader: shows shortened estimated stats with FF

