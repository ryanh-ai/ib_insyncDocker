#!/usr/bin/env python3

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanger,
    aws_iam as iam,
    cdk,
)

SSM_POLICY_STATEMENT = """
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters",
        "kms:Decrypt"
      ],
      "Resource": [
        "arn:aws:ssm:<region>:<aws_account_id>:parameter/parameter_name",
        "arn:aws:kms:<region>:<aws_account_id>:key/key_id"
      ]
    }
  ]
}
"""


class IBC(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        id: str,
        secrets_path: str = "/ibc/paper/",
        trading_mode: str = "paper",
        **kwargs
    ) -> None:
        super().__init__(scope, id, *kwargs)

        # Create a cluster
        vpc = ec2.Vpc.from_lookup(self, "sandbox-VPC", vpc_name="sandbox-VPC")

        privateSubnets = vpc.private_subnets

        # NOTE: secrets manager doesn't allow you to lookup secret by name for ECS yet
        #  EX: '{{resolve:secretsmanager:MySecret:SecretString:password}}'
        #  user = ssm.ParameterStoreSecureString(
        #      parameter_name=secret_prefix + "TWS_USER", version=1
        #  ).to_string()
        #  user = ssm.ParameterStoreString(self, 'user',
        #  parameter_name=secret_prefix + "TWS_USER", version=1
        #  )
        #  user = "{{{{resolve:secretsmanger:{}TWS_USER}}}}".format(secret_prefix)
        #
        #  password = ssm.ParameterStoreString(self, 'password',
        #  parameter_name=secret_prefix + "TWS_PASSWORD", version=1
        #  )
        #  password = "{{{{resolve:secretsmanger:{}TWS_PASSWORD}}}}".format(secret_prefix)
        #
        #  mode = ssm.ParameterStoreString(self, 'mode',
        #  parameter_name=secret_prefix + "TWS_LIVE_PAPER", version=1
        #  )
        #  mode = "{{{{resolve:secretsmanger:{}TWS_LIVE_PAPER}}}}".format(secret_prefix)
        #

        environment = {"SECRETS_PATH": secrets_path, "TWS_LIVE_PAPER": trading_mode}

        cluster = ecs.Cluster(self, "ibctest", vpc=vpc)

        task = ecs.FargateTaskDefinition(
            self, "ibctask", cpu="1024", memory_mi_b="2048"
        )

        #Add SSM Permissions to IAM Role
        SSM_ACTIONS = ["ssm:GetParametersByPath", "kms:Decrypt"]
        SSM_RESOURCES = ["arn:aws:kms:*:*:alias/aws/ssm",
                         "arn:aws:ssm:*:*:parameter{}*".format(secrets_path)]
        ssmPolicy = iam.PolicyStatement(iam.PolicyStatementEffect.Allow)
        for action in SSM_ACTIONS:
            ssmPolicy.add_action(action)
        for resource in SSM_RESOURCES:
            ssmPolicy.add_resource(resource)
        task.add_to_task_role_policy(ssmPolicy)

        ibcRepo = ecr.Repository.from_repository_name(self, "ibcrepo", "ibc")

        ibcImage = ecs.ContainerImage.from_ecr_repository(ibcRepo, "latest")

        ibcContainer = ecs.ContainerDefinition(
            self,
            "ibccontainer",
            task_definition=task,
            image=ibcImage,
            environment=environment,
            logging=ecs.AwsLogDriver(self, "ibc_logger", stream_prefix="ibc_container"),
            essential=True,
        )

        securityGroup = ec2.SecurityGroup.from_security_group_id(
            self, "ibc-sg", security_group_id="sg-2cc6a145"
        )

        ibcService = ecs.FargateService(
            self,
            "ibcservice",
            cluster=cluster,
            task_definition=task,
            assign_public_ip=False,
            desired_count=1,
            security_group=securityGroup,
            # serviceDiscoveryOptions=None,
            service_name="ibc",
            vpc_subnets=privateSubnets,
        )


app = cdk.App()
IBC(app, "ibcfargate-live", secrets_path="/ibc/live/", trading_mode="live")
app.run()
