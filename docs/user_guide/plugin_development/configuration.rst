Configuration
=============

Plugin configuration through the built-in `!config` command
-----------------------------------------------------------

Err can keep a simple python object for the configuration of your
plugin. This avoids the need for admins to configure settings in
some kind of configuration file, instead allowing configuration to
happen directly through chat commands.

In order to enable this feature, you need to provide a configuration
template (ie. a config example) by overriding the
:meth:`~errbot.botplugin.BotPlugin.get_configuration_template`
method. For example, a plugin might request a dictionary with 2
entries:

.. code-block:: python

    from errbot import BotPlugin

    class PluginExample(BotPlugin):
        def get_configuration_template(self):
            return {'ID_TOKEN': '00112233445566778899aabbccddeeff',
                    'USERNAME':'changeme'}

With this in place, an admin will be able to request the default
configuration template with `!config PluginExample`. He or she could
then give the command
`!config PluginExample {'ID_TOKEN' : '00112233445566778899aabbccddeeff', 'USERNAME':'changeme'}`
to enable that configuration.

It will also be possible to recall the configuration template, as
well as the config that is actually set, by issuing `!config
PluginExample` again.

Within your code, the config that is set will be in `self.config`:

.. code-block:: python

    @botcmd
    def mycommand(self, mess, args):
        # oh I need my TOKEN !
        token = self.config['ID_TOKEN']

.. warning::
    If there is no configuration set yet, `self.config` will be
    `None`.


Supplying partial configuration
-------------------------------

Sometimes you want to allow users to only supply a part of the configuration
they wish to override from the template instead of having to copy-paste and
modify the complete entry.

This can be achieved by overriding :meth:`~errbot.botplugin.BotPlugin.configure`:

.. code-block:: python

    from itertools import chain

    CONFIG_TEMPLATE = {'ID_TOKEN': '00112233445566778899aabbccddeeff',
                       'USERNAME':'changeme'}

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CONFIG_TEMPLATE
        super(PluginExample, self).configure(config)

What this achieves is that it creates a Python dictionary object which
contains all the values from our `CONFIG_TEMPLATE` and then updates
that dictionary with the configuration received when calling the
`!config` command. `!config` must be passed a dictionary for this to
work.

If you wish to reset the configuration to its defaults all you need to do is
pass an empty dictionary to `!config`.

You'll now also need to override :meth:`~errbot.botplugin.BotPlugin.get_configuration_template`
and return the `CONFIG_TEMPLATE` in that function:

.. code-block:: python

    def get_configuration_template(self):
        return CONFIG_TEMPLATE


Using custom configuration checks
---------------------------------

By default, Err will check the supplied configuration against the
configuration template, and raise an error if the structure of the
two doesn't match.

You need to override the :meth:`~errbot.botplugin.BotPlugin.check_configuration`
method if you wish do some other form of configuration validation.
This method will be called automatically when an admin configures
your plugin with the `!config` command.

.. warning::
    If there is no configuration set yet, it will pass `None` as
    parameter. Be mindful of this situation.

Using the partial configuration trick as shown above requires you to
override :meth:`~errbot.botplugin.BotPlugin.check_configuration`, so
at a minimum you'll need this:

.. code-block:: python

    def check_configuration(self, configuration):
        pass

We suggest that you at least do some validation instead of nothing but
that is up to you.
