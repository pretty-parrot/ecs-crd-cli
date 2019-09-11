from ecs_crd.canaryReleaseDeployStep import CanaryReleaseDeployStep
from ecs_crd.prepareDeploymentListenersStep import PrepareDeploymentListenersStep

class PrepareDeploymentTargetGroupsStep(CanaryReleaseDeployStep):
    
    def __init__(self, infos, logger):
        """initialize a new instance of class"""
        super().__init__(infos,'Prepare deployment ( Target groups )', logger)

    def _process_target_group_tags(self, item, target_group):
        """update tags informations for the target group"""
        target_group['Properties']['Tags'] = []

        tag = {}
        tag['Key'] = "Environment"
        tag['Value'] = self.infos.environment
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Project"
        tag['Value'] = self.infos.project
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Service"
        tag['Value'] = self.infos.service_name
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Version"
        tag['Value'] = self.infos.service_version
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "Container"
        tag['Value'] = item['ContainerName']
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "ContainerPort"
        tag['Value'] = str(item['ContainerPort'])
        target_group['Properties']['Tags'].append(tag)

        tag = {}
        tag['Key'] = "CanaryRelease"
        tag['Value'] = self.infos.green_infos.canary_release
        target_group['Properties']['Tags'].append(tag)

    def _process_target_group_port(self, item, target_group_info ,target_group):
        """update port informations for the target group"""
        if 'port' in target_group_info:
            if self.is_int(target_group_info['port']):
                target_group['Properties']['Port'] = int(target_group_info['port'])
            else:
                if 'green' in target_group_info['port'] and 'blue' in target_group_info['port']:
                    target_group['Properties']['Port'] = int(target_group_info['port'][self.infos.elected_release])
                else:
                    raise ValueError('Not found port target group informations for container {}:{} '.format(item['ContainerName'],item['ContainerPort']))             
        else:
            target_group['Properties']['Port'] = int(item['ContainerPort'])
        if target_group['Properties']['Port'] < 0:
            raise ValueError('{} is invalid for the port of target group'.format(target_group['Properties']['Port']))
        self.logger.info('      Port: {}'.format(target_group['Properties']['Port']))

    def _process_target_group_protocol(self, item, target_group_info ,target_group):
        """update protocol informations for the target group"""
        if 'protocol' in target_group_info:
            target_group['Properties']['Protocol'] = target_group_info['protocol'].upper()
        else:
            target_group['Properties']['Protocol'] = 'HTTP'
        if target_group['Properties']['Protocol'] not in ['HTTP','HTTPS']:
            raise ValueError('{} is not valid protocle'.format(target_group['Properties']['Protocol']))
        self.logger.info('      Procotol: {}'.format(target_group['Properties']['Protocol']))

    def _process_target_group_attributes(self, item, target_group_info ,target_group):
        """update attributes informations for the target group"""
        if 'target_group_attributes' in target_group_info:
            target_group['TargetGroupAttributes'] = []
            self.logger.info('      Target group attributes:')
            for e in target_group_info['target_group_attributes']:
                target_group_attribute = {}
                target_group_attribute['Key'] = str(e['key'])
                target_group_attribute['Value'] = str(e['value'])
                target_group['TargetGroupAttributes'].append(target_group_attribute)
                self.logger.info('          {}: {}'.format(target_group_attribute['Key'], target_group_attribute['Value']))
    
    def _process_target_group_health_check(self, item,  target_group_info ,target_group):
        """update health check informations for the target group"""
        if 'health_check' not in target_group_info:
            raise ValueError('health_check is mandatory.')
        target_group['Properties']['HealthCheckEnabled']= "true"
        health_check_infos = target_group_info['health_check']
        self.logger.info('      HealthCheck:')
        host_port = self._find_host_port(item['ContainerName'],item['ContainerPort'])
        if host_port != 0:
            # Port
            if 'port' in health_check_infos:
                if self.is_int(health_check_infos['port']):
                    target_group['Properties']['HealthCheckPort'] = int(health_check_infos['port'])
                else:
                    if 'green' in health_check_infos['port'] and 'blue' in health_check_infos['port']:
                        target_group['Properties']['HealthCheckPort'] = int(health_check_infos['port'][self.infos.elected_release])
            self.logger.info('         Host port: {}'.format(target_group['Properties']['HealthCheckPort']))
        else:
            self.logger.info('         Host port: {}'.format('dynamic'))
        # Interval seconds
        if 'interval_seconds' in health_check_infos:
            target_group['Properties']['HealthCheckIntervalSeconds']= int(health_check_infos['interval_seconds'])
            self.logger.info('         Interval Seconds: {}'.format(target_group['Properties']['HealthCheckIntervalSeconds']))

        # Healthy threshold count
        if 'healthy_threshold_count' in health_check_infos:
            target_group['Properties']['HealthyThresholdCount']= int(health_check_infos['healthy_threshold_count'])
            self.logger.info('         Healthy Threshold Count: {}'.format(target_group['Properties']['HealthyThresholdCount']))

        # Unhealthy threshold count
        if 'unhealthy_threshold_count' in health_check_infos:
            target_group['Properties']['UnhealthyThresholdCount']= int(health_check_infos['unhealthy_threshold_count'])
            self.logger.info('         UnHealthy Threshold Count: {}'.format(target_group['Properties']['UnhealthyThresholdCount']))

        # Path
        target_group['Properties']['HealthCheckPath']= '/'               
        if 'path' in health_check_infos:
            target_group['Properties']['HealthCheckPath'] = health_check_infos['path']
        
        self.logger.info('         Path: {}'.format(target_group['Properties']['HealthCheckPath']))
        
        # Protocol
        if 'protocol' in health_check_infos:
            target_group['Properties']['HealthCheckProtocol'] = health_check_infos['protocol'].upper()
        else:
            target_group['Properties']['HealthCheckProtocol']= 'HTTP'

        self.logger.info('         Protocol: {}'.format(target_group['Properties']['HealthCheckProtocol']))

        # Matcher
        matcher = {}
        matcher['HttpCode'] = "200"
        if 'matcher' in health_check_infos:
            matcher['HttpCode'] = health_check_infos['matcher']

        target_group['Properties']['Matcher'] = matcher
        self.logger.info('         Matcher: {}'.format(matcher['HttpCode']))
            
        return host_port

    def _on_execute(self):
        """operation containing the processing performed by this step"""
        try:

            self.logger.info('')
            self.logger.info('Target group infos :')
            self.logger.info(''.ljust(50, '-'))

            cfn = self.infos.green_infos.stack['Resources']['Service']['Properties']['LoadBalancers']
            for item in cfn:

                target_group = {}
                target_group['Type'] = "AWS::ElasticLoadBalancingV2::TargetGroup"
                target_group['Properties'] = {}
                target_group['Properties']['Name'] = ('{}-{}'.format(self.infos.id[:10], item['TargetGroupArn']['Ref'].replace('TargetGroup','')[:18]))+'-tg'
                target_group['Properties']['VpcId'] = self.infos.vpc_id
    
                self._process_target_group_tags(item, target_group)       

                target_group_info = None
                for elmt in self.configuration['target_groups']:
                    container_name = 'default'
                    if 'name' in elmt['container']:
                        container_name = elmt['container']['name']
                    if (elmt['container']['port'] == item['ContainerPort'] 
                        and container_name == item['ContainerName']):
                        target_group_info = elmt
                        break

                if target_group_info == None:
                    raise ValueError('Not found target group informations for container {}:{} '.format(item['ContainerName'],item['ContainerPort'])) 
                
                container_name = 'default' if 'name' not in target_group_info['container'] else target_group_info['container']['name']
                self.logger.info('  Container "{}:{}"'.format(container_name,target_group_info['container']['port']))
                self._process_target_group_port(item, target_group_info, target_group)
                self._process_target_group_protocol(item, target_group_info, target_group)
                self._process_target_group_attributes(item, target_group_info, target_group)
                host_port = self._process_target_group_health_check(item, target_group_info, target_group)
                self.infos.green_infos.stack['Resources'][item['TargetGroupArn']['Ref']] = target_group

            self.infos.save()
            
            return PrepareDeploymentListenersStep(self.infos, self.logger)
  
        except Exception as e:
            self.infos.exit_code = 1
            self.infos.exit_exception = e
            self.logger.error(self.title, exc_info=True)
        else:
            return None

    def _find_host_port(self, container_name, container_port):
        """find the host port for tuple container name/ container port """
        cfn_container_definitions = self.infos.green_infos.stack['Resources']['TaskDefinition']['Properties']['ContainerDefinitions']
        container_info =  next((x for x in cfn_container_definitions if x['Name'] == container_name), None)
        return next((x for x in container_info['PortMappings'] if x['ContainerPort'] == container_port), None)['HostPort']
  
               