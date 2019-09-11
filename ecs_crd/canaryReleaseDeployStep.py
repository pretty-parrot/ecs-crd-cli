from abc import ABC, abstractmethod
import logging
import yaml
import time

class CanaryReleaseDeployStep(ABC):

    def __init__(self, infos, title, logger, with_end_log = True, with_start_log = True):
        self.infos = infos
        self.title = title
        self.logger = logger
        self.with_start_log = with_start_log
        self.with_end_log = with_end_log
        self.previous_exit_code = self.infos.exit_code
        self.configuration = self._load_configuration()

    def execute(self):
        if self.with_start_log: 
            self._log_start()
        result = self._on_execute()
        if self.with_end_log:
             self._log_end()
        return result

    def _log_start(self):
        self.logger.info('')
        self.logger.info(''.ljust(50, '-'))
        self.logger.info(f'Step: {self.title}')
        self.logger.info(''.ljust(50, '-'))
    
    def _log_end(self):
        self.logger.info('')
        result = 'COMPLETED'
        if self.infos.exit_code != 0 and self.previous_exit_code == 0:
            result = 'FAILED'

        self.logger.info(f'{self.title} : {result}')

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def bind_data(self, src):
        if src is None:
            return None
        if self.infos.account_id != None:
            data = src.replace('{{account_id}}', self.infos.account_id)
        if self.infos.environment !=  None:
            data = data.replace('{{environment}}', self.infos.environment)
        if self.infos.region !=  None:
            data = data.replace('{{region}}', self.infos.region)
        if self.infos.project != None:
            data = data.replace('{{project}}', self.infos.project)
        if self.infos.service_name != None:
            data = data.replace('{{name}}', self.infos.service_name)
        if self.infos.service_version != None:
            data = data.replace('{{version}}', self.infos.service_version)
        if self.infos.fqdn !=None:
            data = data.replace('{{fqdn}}', self.infos.fqdn)
        if self.infos.external_ip != None:
            data = data.replace('{{external_ip}}',self.infos.external_ip)
        return data

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def _load_configuration(self):
        with open(self.infos.configuration_file, 'r') as stream:
            return yaml.safe_load(stream)
    #----------------------------------------------------
    #
    #----------------------------------------------------
    def is_int(self, src):
        try:
            int(src)
            return True
        except:
            return False

    #----------------------------------------------------
    #
    #----------------------------------------------------
    @abstractmethod
    def _on_execute(self):
        pass

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def wait(self, wait, label, tick = 5):
        t = 0
        while (t < wait):
            time.sleep(tick)
            t += tick
            r = self.second_to_string(t)
            self.logger.info(f' {label} ... [{r} elapsed]')

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def second_to_string(self, seconds):
        tm = int(seconds)
        day = tm // (24 * 3600)
        tm = tm % (24 * 3600)
        hours = tm // 3600
        tm %= 3600
        minutes = tm // 60
        tm %= 60
        seconds = tm
        result = ''
        if day > 0:
            result += f'{day}d'
        if hours > 0:
            result += f'{day}h'
        if minutes > 0:
            result += f'{minutes}m'
        result += f'{seconds}s'
        return result