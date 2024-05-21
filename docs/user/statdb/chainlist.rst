.. _chainlist

Chain List Generator
====================
The chain list generator generates a list of potential targets based on the specified configuration and your stat score utilizing the available stat records visible to you. For more details about what stats records are available to you to view, take a look at the :ref:`stat database documentation<statdb>`.

.. warning::
    Older target data will not be as accurate as newer target data if the target has been active since the data was recorded. All target data is only for a specific point in time specified by the "Last Updated" time.

Configuration Options
---------------------
.. image:: /_static/images/chain_list_options.png
    :alt: Chain list generator options

There are three following configuration options that are required to be set for a chain list to be generated.

Target Difficulty
`````````````````
The chain list difficulty generates a chain list with a certain ease to defeat determined by the fair fight (FF) multiplier calculated with the stored stat record for the targets.

.. list-table::
    :header-rows: 1

    * - Difficulty Name
      - Minimum FF
      - Maximum FF
      - Notes
    * - Very Easy
      - 1.25
      - 1.75
      - Most users should be able to defeat these targets with a few hits and minimal life loss.
    * - Easy
      - 1.75
      - 2
      -
    * - Medium
      - 2
      - 2.25
      -
    * - Hard
      - 2.25
      - 2.5
      - These targets will provide decent respect without being too hard to defeat.
    * - Very Hard
      - 2.5
      - 3
      - These targets will be difficult to defeat and may cause users to lose a significant amount of life.

Target Sorting
``````````````
The sorting options will order the list of potential targets based on certain criteria.

Recently updated sorting will only return targets whose stat records were added to the database most recently.

Highest respect sorting will only return targets who will provide the most respect if the user attacks them. This respect is based on target data retrieved when the stat record was added to the database; thus, if the target is active, the level and base respect of the target will not be accurate.

Random sorting will randomly retrieve applicable stat records from the database.

.. note::
    Highest respect sorting has an increased latency of up to 10 seconds compared to other sorting options (which respond in less than 1 second typically_ due to the increased load upon the database. So if data is not quickly loaded, be patient and watch for an error notification to be shown.

Target List Limit
`````````````````
The target list limit is the number of potential targets that will be shown. It is recommended that mobile users use a lower limit.

Chain List Results
------------------
.. image:: /_static/images/chain_list_card.png
    :alt: Chain list results

The list of potential targets will be shown as a group of "cards" similar to the above card. The "Last Update" value of the card will show when the target data was last updated. Specific target data can be retrieved by pressing the refresh button. Additional buttons allow the target's profile and attack profile to be loaded.

.. note::
    For security reasons, leaving the chain list page (or any Tornium page) open for too long will de-authenticate the internal API requiring the page to be refreshed.
