Tornium
===================================
.. image:: https://img.shields.io/github/last-commit/Tornium/tornium-core?style=for-the-badge
   :alt: GitHub last commit

Tornium is a Discord bot and website made for `Torn City <https://www.torn.com>`_ built from scratch.

This documentation is still under construction and thus is not yet complete. If you find a missing section and need some help, contact the developer via the links found in the sidebar.

For information on how to keep your Tornium account secure, check out the :ref:`security section<security>`.

API Usage
---------
In accordance with `Torn's official rules for tools <https://www.torn.com/forums.php#/p=threads&f=67&t=16037108&b=0&a=0>`_, no user data will be viewed for any reason beyond security and maintenance. Additionally your API key will only be viewed for maintenance with and only with the permission of the key's owner.

Tornium has automated tasks that will make Torn API calls in addition to calls made by the website and the Discord bot. All API calls originating from Tornium can be identified with the "Tornium" comment.

Features
========
 * Faction banking
 * Stat database with chain list generator
 * Discord Notifications
 * Stocks
 * User Verification
 * And more!!

User Guide
==========
This part of the documentation contains details useful for end users who merely wish to use Tornium instead of participating in its development or hosting it themselves.

.. toctree::
   :maxdepth: 1

   user/quickstart
   user/navigation
   report

Tutorials
=========
Tornium has some tutorials describing how to perform certain actions:

.. toctree::
    :maxdepth: 1

    tutorial/user_discord_id.rst

Userscripts
===========
Tornium has official support for a few userscripts for which support can be found below.

.. toctree::
    :maxdepth: 1

    userscripts/estimate

References
==========
This part of the documentation contains API documentation for Tornium functions, classes, and methods.

This section is currently under construction.

Tornium Extensions
------------------
Tornium extensions allow users to extend Tornium in a limited fashion without contributing to the main repositories. Tornium extensions currently only supports creating new Discord commands and new Flask endpoints. A template for creating new Tornium extensions can be found at `Tornium/tornium-extension-template <https://github.com/Tornium/tornium-extension-template>`_. Any extensions must start with `tornium_` and should be packaged as a Python package.

.. warning::
   Due to Tornium's usage of the Affero General Public License (AGPLv3), extensions are required to released under AGPL or a GPL-compliant license and the source code must be distributed in a GPL-compliant method.

Deprecation Notices
===================
 * Pre-existing stakeouts will be removed (without migration) in the v0.4.x release cycle. Please use stakeouts via Discord slash commands in the future.
