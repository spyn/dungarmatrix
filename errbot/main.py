from os import path, makedirs, sep, getcwd
import logging


def main(bot_class, logger):
    # from here the environment is supposed to be set (daemon / non daemon,
    # config.py in the python path )

    from config import BOT_IDENTITY, BOT_LOG_LEVEL, BOT_DATA_DIR, BOT_LOG_FILE, BOT_LOG_SENTRY
    from errbot.utils import PLUGINS_SUBDIR
    from errbot import holder

    if BOT_LOG_FILE:
        hdlr = logging.FileHandler(BOT_LOG_FILE)
        hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(hdlr)
    logger.setLevel(BOT_LOG_LEVEL)

    if BOT_LOG_SENTRY:
        try:
            from raven.handlers.logging import SentryHandler
        except ImportError as _:
            logging.exception(
                "You have BOT_LOG_SENTRY enabled, but I couldn't import modules "
                "needed for Sentry integration. Did you install raven? "
                "(See http://raven.readthedocs.org/en/latest/install/index.html "
                "for installation instructions)"
            )
            exit(-1)
        from config import SENTRY_DSN, SENTRY_LOGLEVEL

        sentryhandler = SentryHandler(SENTRY_DSN, level=SENTRY_LOGLEVEL)
        logger.addHandler(sentryhandler)

    # make the plugins subdir to store the plugin shelves
    d = BOT_DATA_DIR + sep + str(PLUGINS_SUBDIR)
    if not path.exists(d):
        makedirs(d, mode=0o755)

    holder.bot = bot_class(**BOT_IDENTITY)
    errors = holder.bot.update_dynamic_plugins()
    if errors:
        logging.error('Some plugins failed to load:\n' + '\n'.join(errors))
    logging.debug('serve from %s' % holder.bot)
    holder.bot.serve_forever()
