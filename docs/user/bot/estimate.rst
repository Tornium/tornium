.. _estimate:

Stat Estimation [ALPHA]
=======================
In addition to the stat database, Tornium also supports the estimation of a user's total battle stats. This feature calculates the mentioned user's stat score, so a range of of stats will be produced instead of a specific stat total.

.. warning::
    This feature is resource intensive at the current point in the development cycle. As such, do NOT abuse the bot.

.. note::
    This feature is only available on the officially hosted version of Tornium being a closed-source extension to Tornium. For more information, contact tiksan on Discord.

Accuracy
--------
Due to the limitations of the data used to estimate the math for this feature as well as the math used to calculate range of total battle stats from a stat score, this feature is more accurate for lower battle stats than higher battle stats (especially higher than 3 billion total).

Typically utilizing both an exact stat score and a stat bucket can provide a mostly accurate assessment of a user's total stats.

Estimated Stat Score Accuracy
`````````````````````````````
The accuracy of this feature isn't exactly known due to the limitations of the math used, but is estimated to be around 80%.

Estimate Stat Bucket Accuracy
`````````````````````````````
The accuracy of this feature is around 83% on a test sample of 8,000 users which is higher than that of an exact stat score. But due to the width of a bucket if the result is off by one bucket, the resulting range can be off by hundreds of millions.

Skip the following until the `Stat Estimation Slash Command`_ if you don't want a semi-technical explanation of the accuracy of this feature.

The below image depicts a confusion matrix of the 8,000 tested sample on this feature. The x-axis shows what is estimated to be the stat bucket while the y-axis is the real stat bucket. As depicted, the majority of tested users are estimated to be in the correct bucket and a handful of users are within one bucket of the estimated bucket (often higher than the estimated).

.. image:: /_static/images/estimate_bin_accuracy.png
    :alt: Estimate Stat Bucket Accuracy

However, accuracy of this feature has a higher accuracy in the mid 80s in the lower stat scores (until around 80,000,000 total battle stats). After which, accuracy hovers between 60% and 70%.

.. note::
    This data is effective as of July 4th, 2023. As more data is collected, processed, and analyzed, this feature will grow more accurate.

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
    * - ``type``
      - Estimation type - either ``Estimated Range`` or ``Estimated Value`` (see above)
      - False
      - ``Estimated Range``

Either a Torn ID or a name must be passed to choose a user.