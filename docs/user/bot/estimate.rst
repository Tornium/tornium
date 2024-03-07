.. _estimate:

Stat Estimation
===============
In addition to the stat database, Tornium also supports the estimation of a user's total battle stats. This feature calculates the mentioned user's stat score, so a range of of stats will be produced instead of a specific stat total.

Accuracy
--------
Due to the limitations of the data used to estimate the math for this feature as well as the math used to calculate range of total battle stats from a stat score, this feature is more accurate for lower battle stats than higher battle stats (especially higher than 5 billion total).

Estimated Stat Score Accuracy
`````````````````````````````
The accuracy of this feature isn't exactly known due to the limitations of the math used, but is estimated to be around 90-95%.

Stat Estimation Slash Command
-----------------------------
.. code-block::

    /estimate [tornid] [name] [type]

Estimates the specified user's stat score and total battle stats.

The ``Estimated Range`` type is the default and will use a bucket of stat scores to estimate the range. The ``Estimated Value`` type will estimate the specific stat score.

.. list-table::
    :header-rows: 1

    * - Argument
      - Definition
      - Required
      - Default
    * - ``tornid``
      - Torn user ID
      - False
      -
    * - ``name``
      - Torn user name
      - False
      -

Either a Torn ID or a name must be passed to choose a user.
