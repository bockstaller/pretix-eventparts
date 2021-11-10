pretix eventparts
==========================

This plugin allows you to assign participants to different parts/stages of your event and communicate this to them.
Especially for events following the Roverway or rover**voco** structure, where you have one or more kickoffs to start with,
a middlepart where small groups of participants have their individual experiences/workshops/projects and a common closing camp.
You can:
- create eventparts and assign them the start, middle and end position, tag them, add descriptions and a capacity
- assign orders to these eventparts from the order view
- see all assigned orders from the eventparts view
- publish the assigned eventparts and their descriptions to the customers order info page and include the information on their ticket

Development setup
-----------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

This plugin has CI set up to enforce a few code style rules. To check locally, you need these packages installed::

    pip install flake8 isort black docformatter

To check your plugin for rule violations, run::

    docformatter --check -r .
    black --check .
    isort -c .
    flake8 .

You can auto-fix some of these issues by running::

    docformatter -r .
    isort .
    black .

To automatically check for these issues before you commit, you can run ``.install-hooks``.


License
-------


Copyright 2021 Lukas Bockstaller

Released under the terms of the Apache License 2.0



.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
