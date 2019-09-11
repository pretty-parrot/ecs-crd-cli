import os
import uuid
import datetime
import json
import hashlib
import re

from ecs_crd.defaultJSONEncoder import DefaultJSONEncoder

class ScaleInfos:
     def __init__(self, desired, wait):
        self.desired = desired
        self.wait = wait

class StrategyInfos:
    def __init__(self, weight, wait):
        self.weight = weight
        self.wait = wait

class PolicyInfos:
    def __init__(self, name, effect, action, resource):
        self.name = name
        self.effect = effect
        self.action = action
        self.resource = resource

class InitInfos:
    def __init__(self):
        self.stack_id = None
        self.stack_name = None
        self.stack = None
        self.file_name = None

class ReleaseInfos(InitInfos):
    def __init__(self):
        super().__init__()
        self.alb_arn = None
        self.alb_dns = None
        self.alb_hosted_zone_id = None
        self.canary_release = None

class LoadBalancerInfos:
    def __init__(self, arn, dns_name, canary_release, hosted_zone_id ):
        self.arn = arn
        self.dns_name = dns_name
        self.canary_release = canary_release
        self.is_elected = False
        self.hosted_zone_id = hosted_zone_id

class ListenerRuleInfos:
    def __init__(self, listener_arn, configuration):
        self.listener_arn = listener_arn
        self.configuration = configuration

class SecretInfos:
    def __init__(self):
        self.secrets = []
        self.kms_arn = []
        self.secrets_arn = [] 

class ContainerDefinitionsInfos:
        def __init__(self):
            self.ports = []
            self.image = None
            self.cpu = 128
            self.memmory = 128
            self.environment = []
            self.secrets = []

class CanaryReleaseInfos:
    def __init__(self, environment, region, configuration_file):
        self.id = uuid.uuid4().hex
        self.action = None
        self.account = None
        self.external_ip = None
        self.exit_code = 0
        self.exit_exception = None
        self.canary_group = None
        self.cluster_name = None
        self.cluster = None
        self.region = region
        self.environment = environment
        self.project = None
        self.service_name = None
        self.service_version = None
        self.listener_port = None
        self.fqdn = None
        self.hosted_zone_id = None
        self.vpc_id = None
        self.scale_infos = None
        self.configuration_file = configuration_file
        self.strategy_infos = []
        self.init_infos = InitInfos()
        self.init_infos.stack = self._load_init_cloud_formation_template()
        self.green_infos = ReleaseInfos()
        self.green_infos.stack = self._load_green_cloud_formation_template()
        self.blue_infos = None
        self.listener_rules_infos = []
        self.secrets_infos = None
        self.elected_release = None
        self.ecs_crd_version =self._get_version()
        self.created_date = datetime.datetime.now().strftime('%FT%T%.000Z')

    def _get_version(self):
        module_path = os.path.abspath(os.path.dirname(__file__))
        version_file = open(os.path.join(module_path,'__init__.py'), 'r').read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
        return version_match.group(1)
    
    def _load_green_cloud_formation_template(self):
        result = None
        filename = os.path.dirname(os.path.realpath(__file__))+'/cfn_green_release_deploy.json'
        with open(filename, 'r') as file:
            data = file.read()
            result = json.loads(data)
        result['Parameters']['Environment']['Default'] = self.environment
        result['Parameters']['Region']['Default'] = self.region
        return result

    def _load_init_cloud_formation_template(self):
        result = None
        filename = os.path.dirname(os.path.realpath(__file__))+'/cfn_init_release_deploy.json'
        with open(filename, 'r') as file:
            data = file.read()
            result = json.loads(data)
        result['Parameters']['Environment']['Default'] = self.environment
        result['Parameters']['Region']['Default'] = self.region
        return result
    
    def save(self):
        if not os.path.exists('.deploy-cache'):
            os.mkdir('.deploy-cache')
        if not os.path.exists('.deploy-cache/'+self.id):
            os.mkdir('.deploy-cache/'+self.id)
        with open('.deploy-cache/'+ self.id +'/deploy_info.json', 'w') as file:
            file.write(json.dumps(self, cls= DefaultJSONEncoder, indent= 4))

    def get_hash(self):
        data = f'{self.canary_group}#{self.service_name}#{self.environment}#{self.region}'
        hash_object = hashlib.md5(data.encode())
        return hash_object.hexdigest()
