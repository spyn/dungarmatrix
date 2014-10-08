import json
from errbot import botcmd, BotPlugin, PY2

if PY2:
    from urllib2 import urlopen, quote
else:
    from urllib.request import urlopen, quote


class OctopusDeployBot(BotPlugin):
    min_err_version = '1.6.0'

    def get_configuration_template(self):
        return {'OCTO_API_URL': 'http://<your-octopus-installation>/api',
        		'OCTO_API_KEY': 'API_KEY_HERE'}

    def configure(self, configuration):
        if configuration:
            if type(configuration) != dict:
                raise Exception('Wrong configuration type')

            if not configuration.has_key('OCTO_API_URL'):
                raise Exception('You kinda need to enter the Octopus location, OCTO_URL')

            if not configuration.has_key('OCTO_API_KEY'):
            	raise Exception('You really do need to put your API key in the config, OCTO_API_KEY')

            if len(configuration) > 2:
                raise Exception('What else did you try to insert in my config ?')

        super(OctopusDeployBot, self).configure(configuration)

    @botcmd
    def octodeploy(self, mess, args):
        """
        Run some commands for octodeploy
        """
        if not args:
            return 'What do you expect me to do?'
        if not self.config:
            return 'This plugin needs to be configured... run !config OctopusDeploy'

        api_key = self.config.get('OCTO_API_KEY', None)
        if api_key is None:
            return 'Invalid API KEY'

        api_url = self.config.get('OCTO_API_URL', None)
        if api_url is None:
        	return 'Invalid API URL'

   		return "TODO"
