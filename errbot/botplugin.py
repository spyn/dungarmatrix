import logging
import os
from threading import Timer, current_thread
from errbot.utils import PLUGINS_SUBDIR, recurse_check_structure
from errbot.storage import StoreMixin, StoreNotOpenError
from errbot import holder


class BotPluginBase(StoreMixin):
    """
     This class handle the basic needs of bot plugins like loading, unloading and creating a storage
     It is the main contract between the plugins and the bot
    """

    def __init__(self):
        self.plugin_dir = holder.bot.plugin_dir
        self.is_activated = False
        self.current_pollers = []
        self.current_timers = []
        super(BotPluginBase, self).__init__()

    def activate(self):
        """
            Override if you want to do something at initialization phase (don't forget to
            super(Gnagna, self).activate())
        """
        from config import BOT_DATA_DIR

        classname = self.__class__.__name__
        logging.debug('Init storage for %s' % classname)
        filename = BOT_DATA_DIR + os.sep + PLUGINS_SUBDIR + os.sep + classname + '.db'
        logging.debug('Loading %s' % filename)
        self.open_storage(filename)
        holder.bot.inject_commands_from(self)
        self.is_activated = True

    def deactivate(self):
        """
            Override if you want to do something at tear down phase (don't forget to super(Gnagna, self).deactivate())
        """
        if self.current_pollers:
            logging.debug('You still have active pollers at deactivation stage, I cleaned them up for you.')
            self.current_pollers = []
            for timer in self.current_timers:
                timer.cancel()

        try:
            self.close_storage()
        except StoreNotOpenError:
            pass
        holder.bot.remove_commands_from(self)
        self.is_activated = False

    def start_poller(self, interval, method, args=None, kwargs=None):
        if not kwargs:
            kwargs = {}
        if not args:
            args = []

        logging.debug('Programming the polling of %s every %i seconds with args %s and kwargs %s' % (
            method.__name__, interval, str(args), str(kwargs))
        )
        # noinspection PyBroadException
        try:
            self.current_pollers.append((method, args, kwargs))
            self.program_next_poll(interval, method, args, kwargs)
        except Exception as _:
            logging.exception('failed')

    def stop_poller(self, method, args=None, kwargs=None):
        if not kwargs:
            kwargs = {}
        if not args:
            args = []
        logging.debug('Stop polling of %s with args %s and kwargs %s' % (method, args, kwargs))
        self.current_pollers.remove((method, args, kwargs))

    def program_next_poll(self, interval, method, args, kwargs):
        t = Timer(interval=interval, function=self.poller,
                  kwargs={'interval': interval, 'method': method, 'args': args, 'kwargs': kwargs})
        self.current_timers.append(t)  # save the timer to be able to kill it
        t.setName('Poller thread for %s' % type(method.__self__).__name__)
        t.setDaemon(True)  # so it is not locking on exit
        t.start()

    def poller(self, interval, method, args, kwargs):
        previous_timer = current_thread()
        if previous_timer in self.current_timers:
            logging.debug('Previous timer found and removed')
            self.current_timers.remove(previous_timer)

        if (method, args, kwargs) in self.current_pollers:
            # noinspection PyBroadException
            try:
                method(*args, **kwargs)
            except Exception as _:
                logging.exception('A poller crashed')
            self.program_next_poll(interval, method, args, kwargs)


class BotPlugin(BotPluginBase):
    @property
    def min_err_version(self):
        """
        If your plugin has a minimum version of err it needs to be on in order to run,
        please override accordingly this method, returning a string with the dotted
        minimum version. It MUST be in a 3 dotted numbers format or None

        For example: "1.2.2"
        """
        return None

    @property
    def max_err_version(self):
        """
        If your plugin has a maximal version of err it needs to be on in order to run,
        please override accordingly this method, returning a string with the dotted
        maximal version. It MUST be in a 3 dotted numbers format or None

        For example: "1.2.2"
        """
        return None

    def get_configuration_template(self):
        """
        If your plugin needs a configuration, override this method and return
        a configuration template.

        For example a dictionary like:
        return {'LOGIN' : 'example@example.com', 'PASSWORD' : 'password'}

        Note: if this method returns None, the plugin won't be configured
        """
        return None

    def check_configuration(self, configuration):
        """
        By default, this method will do only a BASIC check. You need to override
        it if you want to do more complex checks. It will be called before the
        configure callback. Note if the config_template is None, it will never
        be called.

        It means recusively:
        1. in case of a dictionary, it will check if all the entries and from
           the same type are there and not more.
        2. in case of an array or tuple, it will assume array members of the
           same type of first element of the template (no mix typed is supported)

        In case of validation error it should raise a errbot.utils.ValidationException
        """
        recurse_check_structure(self.get_configuration_template(), configuration)  # default behavior

    def configure(self, configuration):
        """
        By default, it will just store the current configuation in the self.config
        field of your plugin. If this plugin has no configuration yet, the framework
        will call this function anyway with None.

        This method will be called before activation so don't expect to be activated
        at that point.
        """
        self.config = configuration

    def activate(self):
        """
            Triggered on plugin activation.

            Override this method if you want to do something at initialization phase
            (don't forget to `super().activate()`).
        """
        super(BotPlugin, self).activate()

    def deactivate(self):
        """
            Triggered on plugin deactivation.

            Override this method if you want to do something at tear-down phase
            (don't forget to `super().deactivate()`).
        """
        super(BotPlugin, self).deactivate()

    def callback_connect(self):
        """
            Triggered when the bot has successfully connected to the chat network.

            Override this method to get notified when the bot is connected.
        """
        pass

    def callback_message(self, message):
        """
            Triggered on every message not coming from the bot itself.

            Override this method to get notified on *ANY* message.

            :param message:
                An instance of :class:`~errbot.backends.base.Message`
                representing the message that was received.
        """
        pass

    def callback_presence(self, presence):
        """
            Triggered on every presence change.

            :param message:
                An instance of :class:`~errbot.backends.base.Presence`
                representing the new presence state that was received.
        """
        pass

    def callback_stream(self, stream):
        """
            Triggered asynchronously (in a different thread context) on every incoming stream
            request or file transfert requests.
            You can block this call until you are done with the stream.
            To signal that you accept / reject the file, simply call stream.accept()
            or stream.reject() and return.
            :param stream:
                the incoming stream request.
        """
        stream.reject()  # by default, reject the file as the plugin doesn't want it.

    def callback_botmessage(self, message):
        """
            Triggered on every message coming from the bot itself.

            Override this method to get notified on all messages coming from
            the bot itself (including those from other plugins).

            :param message:
                An instance of :class:`~errbot.backends.base.Message`
                representing the message that was received.
        """
        pass

    def callback_presence(self, presence):
        """
            Triggered on every presence change event.

            Override to get a notification when a contact changes its presence
            status.

            :param presence:
                An instance of :class:`~errbot.backends.base.Presence`
                representing the presence that was received.
        """
        pass

    # Proxyfy some useful tools from the motherbot
    # this is basically the contract between the plugins and the main bot

    def warn_admins(self, warning):
        """
            Sends a warning to the administrators of the bot
        """
        return holder.bot.warn_admins(warning)

    def send(self, user, text, in_reply_to=None, message_type='chat'):
        """
            Sends asynchronously a message to a room or a user.
             if it is a room message_type needs to by 'groupchat' and user the room.
        """
        return holder.bot.send(user, text, in_reply_to, message_type)

    def send_stream_request(self, user, fsource, name=None, size=None, stream_type=None):
        """
            Sends asynchronously a stream/file to a user.
            user is the jid of the person you want to send it to.
            fsource is a file object you want to send.
            name is an optional filename for it.
            size is optional and is the espected size for it.
            stream_type is optional for the mime_type of the content.

            It will return a Stream object on which you can monitor the progress of it.
        """
        return holder.bot.send_stream_request(user, fsource, name, size, stream_type)

    def bare_send(self, xmppy_msg):
        """
            A bypass to send directly a crafted xmppy message.
              Usefull to extend to bot in not forseen ways.
        """
        c = holder.bot.connect()
        if c:
            return c.send(xmppy_msg)
        logging.warning('Ignored a message as the bot is not connected yet')
        return None  # the bot is not connected yet

    def join_room(self, room, username=None, password=None):
        """
            Make the bot join a room
        """
        return holder.bot.join_room(room, username, password)

    def invite_in_room(self, room, jids_to_invite):
        """
            Make the bot invite a list of jids to a room
        """
        return holder.bot.invite_in_room(room, jids_to_invite)

    def get_installed_plugin_repos(self):
        """
            Get the current installed plugin repos in a dictionary of name / url
        """
        return holder.bot.get_installed_plugin_repos()

    def start_poller(self, interval, method, args=None, kwargs=None):
        """
            Start to poll a method at specific interval in seconds.

            Note: it will call the method with the initial interval delay for the first time
            Also, you can program
            for example : self.program_poller(self,30, fetch_stuff)
            where you have def fetch_stuff(self) in your plugin
        """
        super(BotPlugin, self).start_poller(interval, method, args, kwargs)

    def stop_poller(self, method=None, args=None, kwargs=None):
        """
            stop poller(s).

            If the method equals None -> it stops all the pollers
            you need to regive the same parameters as the original start_poller to match a specific poller to stop
        """
        super(BotPlugin, self).stop_poller(method, args, kwargs)
