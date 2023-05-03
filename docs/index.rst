.. Tornium documentation master file, created by
   sphinx-quickstart on Wed Apr 19 12:13:19 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tornium
===================================
.. image:: https://img.shields.io/github/license/Tornium/tornium-core?style=for-the-badge
   :alt: License Badge

.. image:: https://img.shields.io/github/last-commit/Tornium/tornium-core?style=for-the-badge
   :alt: GitHub last commit

Tornium is a Discord bot and website made for `Torn City <https://www.torn.com>`_ built from scratch with love <3.

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

Tutorials
=========
This section is currently under construction.

References
==========
This part of the documentation contains API documentation for Tornium functions, classes, and methods.

This section is currently under construction.

Tornium Extensions
==================
Tornium extensions allow users to extend Tornium in a limited fashion without contributing to the main repositories. Tornium extensions currently only supports creating new Discord commands and new Flask endpoints. A template for creating new Tornium extensions can be found at `Tornium/tornium-extension-template <https://github.com/Tornium/tornium-extension-template>`_. Any extensions must start with `tornium_` and should be packaged as a Python package.

.. warning::
   Due to Tornium's usage of the Affero General Public License (AGPLv3), extensions are required to released under AGPL or a GPL-compliant license and the source code must be distributed in a GPL-compliant method.

Help
====
If you need any help setting up or contributing to Tornium, please contact tiksan on
`Discord <https://discord.com/users/695828257949352028>`_ or `Torn <https://torn.com/profiles.php?XID=2383326>`_.

Deprecation Notices
===================

 * Pre-existing stakeouts will be removed (without migration) in the v0.4.x release cycle. Please use stakeouts via Discord slash commands in the future.
 * Assist request forwarding options will be removed in the v0.5.x release cycle in favor of a permanent whitelist.