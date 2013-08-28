# Copyright (C) [2013] [The FURTHeR Project]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement
from fabric.api import local, lcd, prompt
from os import walk
from os.path import join
from ConfigParser import ConfigParser

import fileinput
import sys
import string
import random
import re

def deployFurtherCore(environment):
	"""Deploy further-core to a given environment where environment is represented as a folder with configuration. This command is meant to be run locally"""
	version = prompt("FURTHeR version to deploy?")
	config = _load_configuration(environment, 'further-core.ini')
	config['version'] = version
	_replace_tokens('further-core/' + environment, config)
	_deploy_further_configuration(environment)

def deployFurtherI2b2(environment):
	"""Deploy further-core to a given environment where environment is represented as a folder with configuration. This command is meant to be run locally"""

	config = _load_configuration(environment, 'further-i2b2.ini')
	_replace_tokens('further-i2b2/' + environment, config)
	_deploy_i2b2_configuration(environment)
	_deploy_further_i2b2_hook(environment)
	_deploy_jboss_configuration(environment)

def _deploy_i2b2_configuration(environment):
	"""Deploys the i2b2 configuration to the i2b2 server environment. This function is meant to be run locally and relies on $JBOSS_HOME, $TOMCAT_HOME, and SRC_HOME being configured"""

	with lcd('further-i2b2'):
		with lcd(environment):
			with lcd('edu.harvard.i2b2.crc'):
				local('cp *-ds.xml $JBOSS_HOME/server/default/deploy')
				local('cp CRCApplicationContext.xml $JBOSS_HOME/server/default/conf/crcapp')
			with lcd('edu.harvard.i2b2.crc.loader'):
				local('cp CRCLoaderApplicationContext.xml $JBOSS_HOME/server/default/conf/crcloaderapp')
			with lcd('edu.harvard.i2b2.ontology'):
				local('cp *-ds.xml $JBOSS_HOME/server/default/deploy')
			with lcd('edu.harvard.i2b2.pm'):
				with lcd('database'):
					local('cp hibernate.properties $TOMCAT_HOME/webapps/gridsphere/WEB-INF/CustomPortal/database')
				with lcd('persistence'):
					local('cp hibernate.properties $TOMCAT_HOME/webapps/default/WEB-INF/persistence')
				local('cp secret.properties $TOMCAT_HOME/webapps/axis2/WEB-INF/classes/')
			with lcd('edu.harvard.i2b2.workplace'):
				local('cp *-ds.xml $JBOSS_HOME/server/default/deploy')
			with lcd('i2b2-webclient'):
				local('rm -rf /var/www/html/i2b2')
				local('cp -R $SRC_HOME/i2b2-webclient/src/main/webapp/i2b2 /var/www/html')
				local('cp i2b2config.ini.php /var/www/html/i2b2/includes')
	
def _deploy_further_i2b2_hook(environment):
	"""Deploys the further-i2b2-hook that is responsible for sending i2b2 queries to be processed by FURTHeR. Relies on $JBOSS_HOME being configured"""

	with lcd('further-i2b2'):
		with lcd(environment):
			with lcd('i2b2-hook'):
				local('cp further.properties $JBOSS_HOME/server/default/deploy/i2b2.war/WEB-INF/classes')

	# Remove old jars
	with lcd('$JBOSS_HOME/server/default/deploy/i2b2.war/WEB-INF'):
		local('rm -rf lib/core-*')
		local('rm -rf lib/i2b2-hook-further*')
		local('rm -rf lib/slf4j-*')
		local('rm -rf fqe-ds-api*')
		
	with lcd('$SRC_HOME/i2b2-hook/i2b2-hook-further/target'):
		tmp_dir = 'hook-tmp'
		local('rm -rf ' + tmp_dir)
		local('mkdir ' + tmp_dir)
		local('cp i2b2-hook-further-bin.zip ' + tmp_dir);
		with lcd(tmp_dir):
			local('unzip i2b2-hook-further-bin.zip')
			with lcd('i2b2-hook-further'):
				local('mv *.jar $JBOSS_HOME/server/default/deploy/i2b2.war/WEB-INF/lib')
				local('mv web.xml.further $JBOSS_HOME/server/default/deploy/i2b2.war/WEB-INF/web.xml')

def _deploy_jboss_configuration(environment):
	with lcd('further-i2b2'):
		with lcd(environment):
			with lcd('jboss'):
				with lcd('jmx-console'):
					local('cp *.xml $JBOSS_HOME/server/default/deploy/jmx-console.war/WEB-INF')
				with lcd('props'):
					local('cp *.properties $JBOSS_HOME/server/default/conf/props')
				with lcd('web-console'):
					local('cp *.xml $JBOSS_HOME/server/default/deploy/management/console-mgr.sar/web-console.war/WEB-INF')
					local('cp *.properties $JBOSS_HOME/server/default/deploy/management/console-mgr.sar/web-console.war/WEB-INF/classes')

def _deploy_further_configuration(environment):
	"""Deploy the further-core configuration. Relies on $ESB_HOME being configured"""
	with lcd('further-core'):
		with lcd(environment):
			local('cp *.cfg $ESB_HOME/etc')
			local('cp *.properties $ESB_HOME/etc')

def _load_configuration(environment, path):
        """Loads a given configuration file specified by path and environment header (ini file).
        returns a key value representing the configuration. Values enclosed in {} are automatically
        decrypted using the $FURTHER_PASSWORD variable. Values that equal [RND] will be replaced with
        a random string."""

        # Read configuration file
        parser = ConfigParser()
        parser.read(path)

        config = {}
        for option in parser.options(environment):
                value = parser.get(environment, option)

                # Handle encrypted configuration
                if (re.match(r'^\{.*\}$', value)):
                        encrypted_value = re.match(r'^\{(.*)\}$', value).group(1)
                        value = (local('decrypt.sh input="' + encrypted_value + '" password=$FURTHER_PASSWORD algorithm="PBEWithSHA1AndDESede" verbose="false"', capture=True))

                # Handle random values
                if (re.match(r'\[RND\]', value)):
                        value = _random_string()

                config[option] = value;

        return config

def _replace_tokens(path, config):
        """Recursively walks the given path and replaces any tokens (@value@) with
        given values within the configuration"""

        replace_tokens = config.keys()
        for dirname, dirnames, filenames in walk(path):
                for filename in filenames:
                        for line in fileinput.input(join(dirname, filename), inplace=True):
                                newline = line
                                for token in replace_tokens:
                                        replace = '@' + token.upper() + '@'
                                        if replace in line:
                                                newline = line.replace(replace, config.get(token))
                                                break
                                sys.stdout.write(newline)

def _random_string(characters=string.ascii_uppercase + string.ascii_lowercase + string.digits, size=32):
        """Generates a random string from all upper, lower, and digits"""
        return ''.join(random.choice(characters) for x in range(size))
