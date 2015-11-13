import sys
import os
import yaml
import argparse
import logging
import subprocess
import re

class Options:
    def __init__(self, args):
        self.parser = argparse.ArgumentParser(description="Run Maven commands for projects")
        self.args = args
        #parser.add_argument('-s', '--switch', dest='switchnetworks', action='store_true')
        self.parser.add_argument('--loglevel', '--loglvl',dest='loglevel',default='info',action='store',choices=["DEBUG","INFO","WARN", "ERROR"], help='Sets loglevel to given level')
        self.parser.add_argument('--logFormat', dest='logFormat', default='[%(levelname)s] %(message)s', action='store', help='Set the logging format')
        self.parser.add_argument('-v','--verbose', action='store_true', help='Sets loglevel to debug')
        self.parser.add_argument('-d', '--dir', dest='workingDir', action='store', default=os.getcwd(), help='Base directory to use for running in mass')
        self.parser.add_argument('--config', dest="config", default="mvnrun.yml", help='Path to mvnrun.yml')
        self.parser.add_argument('-p', '--mvn-path', dest='mavenPath', default='"C:\\Program Files\\Apache Software Foundation\\apache-maven-3.0.5\\bin\\mvn.bat"', help='Path to maven executable')
        self.parser.add_argument('--dry', '--dryrun', '--dry-run', dest='dryrun', action='store_true', help='This flag indicates a dry run the maven commands will be displayed but not executed.')
        self.parser.add_argument('--show-maven-output', dest='showMavenOutput', action='store', choices=["Always", "Fail", "Never"], default='Fail', help='This flag indicates if the maven output should "ALWAYS" be shown, only be shown on build "FAIL", or "Never" be shown.')

        self.options = self.parser.parse_args()

    def get_options(self):
        return self.options
    def get_parser(self):
        return self.parser

class Config(object):
    def __init__(self, filepath):
        self.__filepath = filepath

    def loadConfig(self):
        pass
    def parseConfig(self):
        pass

class YamlConfig(Config):

    def __init__(self, filepath):
        self.config = {}
        self.filepath = filepath
        print self.filepath

    def loadConfig(self):
        with open(self.filepath, 'r') as stream:
            self.config = yaml.load(stream)

    def parseConfig(self):
        return self.config


class Mvnrun:

    def __init__(self,options):
        self.BUILDSUCCESS = 'BUILD SUCCESS'
        self.BUILDFAILURE = 'BUILD FAUILURE'
        self.options = options
        if self.options.config:
            self.config_path = self.options.config
            self.init_config_file()
        self.init_options()
        self.init_logging()

    def init_config_file(self):
        """ Process values in config file """
        self.config = YamlConfig(self.config_path)
        self.config.loadConfig()
        self.config = self.config.parseConfig()

    def init_options(self):
        """ Process Command line options """
        # Setable Values
        if self.options.loglevel:
            self.loglevel = self.options.loglevel
        else:
            self.loglevel = "ERROR"
        if self.options.verbose:
            self.loglevel = "DEBUG"
        if self.options.logFormat:
            self.logFormat = self.options.logFormat
        if self.options.mavenPath:
            self.mavenPath = self.options.mavenPath
        if self.options.workingDir:
            self.workingDir = self.options.workingDir
        showMaven = self.options.showMavenOutput.upper()
        if showMaven == "ALWAYS":
            self.showMavenOutput = True;
        elif showMaven == "FAIL":
            self.onBuildFailureShowMavenOutput = True
            self.showMavenOutputbool = False
        else: # showMaven = Never
            self.showMavenOutput = False;

        # Flags
        self.dryrun = self.options.dryrun

    def init_logging(self):
        numeric_level  = getattr(logging, self.loglevel.upper(),None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: {0}'.format(self.loglevel))

        logging.basicConfig(level=numeric_level,format=self.logFormat)

    def executeCmd(self, cmd):
        logging.debug(cmd)
        if not self.dryrun:
            mvn_process = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            process_output, _ = mvn_process.communicate()
            reg = '{0}|{1}'.format(self.BUILDSUCCESS,self.BUILDFAILURE)
            m = re.search(reg,process_output)
            if not m:
                logging.warn('Error during Processing!')
                self.showMavenOutput(process_output)
                return False
            else:
                if m.group(0) == self.BUILDSUCCESS:
                    self.onBuildSuccess(process_output)
                else: # m.group(0) = self.BUILDFAILURE
                    self.onBuildFailure(process_output)
        return True


    def buildMavenCommandFromlist(self, commandOptions):
        optstr = " ".join(commandOptions)
        return " ".join([self.mavenPath,optstr])

    def onBuildSuccess(self,output):
        logging.info(self.BUILDSUCCESS)#log in green

    def onBuildFailure(self, output):
        logging.warn(self.BUILDFAILURE)#log in red/orange
        self.showMavenOutPut(output)
        if self.onBuildFailureFailOut:
            pass # not sure if this should go here...

    def showMavenOutput(self, output):
        if self.onBuildFailureShowMavenOutput or self.showMavenOutputbool: # this logic needs to be re-assesed
            logging.info(output)

    def main(self):
        print self.config
        mavencfgs = self.config["MavenConfigs"]
        for cfgObj in mavencfgs:
            for cfg in cfgObj:
                origwd = os.getcwd()
                try:
                    os.chdir(os.path.join(self.workingDir,cfg))
                    for goalsobj in cfgObj[cfg]:
                        cmd = self.buildMavenCommandFromlist(goalsobj)
                        self.executeCmd(cmd)
                        os.chdir(origwd)
                except Exception as e:
                    logging.warning(e)
                finally:
                    os.chdir(origwd)

if __name__ == '__main__':
    options = Options(sys.argv).get_options()
    mvnrun = Mvnrun(options)
    mvnrun.main()
