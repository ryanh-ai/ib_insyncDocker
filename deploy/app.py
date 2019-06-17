#!/usr/bin/env python3

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanger,
    aws_iam as iam,
    aws_servicediscovery as servicediscovery,
    aws_logs as logs,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
    cdk,
)


class IBC(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        id: str,
        name: str,
        vpc_name: str,
        security_group_name: str,
        secrets_path: str = "/ibc/paper/",
        trading_mode: str = "paper",
        **kwargs
    ) -> None:
        super().__init__(scope, id, *kwargs)

        # TODO: Create Log Group

        # Create a cluster
        vpc = ec2.Vpc.from_lookup(self, "vpc", vpc_name=vpc_name)

        privateSubnets = vpc.private_subnets

        cluster = ecs.Cluster(self, "cluster", vpc=vpc)
        # TODO: check for namespace before adding below.  This is failing on stack updates.
        cluster.add_default_cloud_map_namespace(name="private")

        task = ecs.FargateTaskDefinition(self, "task", cpu="512", memory_mi_b="1024")

        # Add SSM Permissions to IAM Role
        SSM_ACTIONS = ["ssm:GetParametersByPath", "kms:Decrypt"]
        SSM_RESOURCES = [
            "arn:aws:kms:*:*:alias/aws/ssm",
            "arn:aws:ssm:*:*:parameter{}*".format(secrets_path),
        ]
        ssmPolicy = iam.PolicyStatement(iam.PolicyStatementEffect.Allow)
        for action in SSM_ACTIONS:
            ssmPolicy.add_action(action)
        for resource in SSM_RESOURCES:
            ssmPolicy.add_resource(resource)
        task.add_to_task_role_policy(ssmPolicy)

        ibcRepo = ecr.Repository.from_repository_name(self, "container_repo", "ibc")

        ibcImage = ecs.ContainerImage.from_ecr_repository(ibcRepo, "latest")

        # TODO: Add to Existing Hierarchal Logger, add log_group argument with ref to it
        ibcLogger = ecs.AwsLogDriver(self, "logger", stream_prefix=name)

        connectionLossMetric = logs.MetricFilter(
            self,
            "connectionLossMetric",
            filter_pattern=logs.FilterPattern.literal("ERROR ?110 ?130"),
            log_group=ibcLogger.log_group,
            metric_name="ib_connection_loss",
            metric_namespace=name,
        )

        newContainerMetric = logs.MetricFilter(
            self,
            "newContainerMetric",
            filter_pattern=logs.FilterPattern.literal(
                "Starting virtual X frame buffer"
            ),
            log_group=ibcLogger.log_group,
            metric_name="new_container",
            metric_namespace=name,
        )

        kinesisFirehoseBucketActions = [
            "s3:AbortMultipartUpload",
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:ListBucket",
            "s3:ListBucketMultipartUploads",
        ]

        kinesisFirehoseBucket = s3.Bucket(self, "firehoseBucket")

        kinesisFirehoseBucketPolicy = iam.PolicyStatement(
            iam.PolicyStatementEffect.Allow
        )
        for action in kinesisFirehoseBucketActions:
            kinesisFirehoseBucketPolicy.add_action(action)
        for resource in [
            kinesisFirehoseBucket.bucket_arn,
            kinesisFirehoseBucket.bucket_arn + "/*",
        ]:
            kinesisFirehoseBucketPolicy.add_resource(resource)

        kinesisFirehoseBucketRole = iam.Role(
            self,
            "kinesisFirehoseBucketRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            path="/service/" + name + "/",
        )
        kinesisFirehoseBucketRole.add_to_policy(kinesisFirehoseBucketPolicy)

        kinesisFirehose = firehose.CfnDeliveryStream(
            self,
            "firehose",
            delivery_stream_name=name,
            delivery_stream_type="DirectPut",
            s3_destination_configuration={
                "bucketArn": kinesisFirehoseBucket.bucket_arn,
                "bufferingHints": {"intervalInSeconds": 10 * 60, "sizeInMBs": 16},
                "compressionFormat": "GZIP",
                "roleArn": kinesisFirehoseBucketRole.role_arn,
            },
        )

        # Add Firehose Permissions to Task IAM Role
        FIREHOSE_ACTIONS = ["firehose:PutRecord", "firehose:PutRecordBatch"]
        firehosePolicy = iam.PolicyStatement(iam.PolicyStatementEffect.Allow)
        for action in FIREHOSE_ACTIONS:
            firehosePolicy.add_action(action)
        firehosePolicy.add_resource(kinesisFirehose.delivery_stream_arn)
        task.add_to_task_role_policy(firehosePolicy)

        environment = {
            "SECRETS_PATH": secrets_path,
            "TWS_LIVE_PAPER": trading_mode,
            "FIREHOSE_STREAM_NAME": kinesisFirehose.delivery_stream_name,
        }

        ibcContainer = ecs.ContainerDefinition(
            self,
            "container",
            task_definition=task,
            image=ibcImage,
            environment=environment,
            logging=ibcLogger,
            essential=True,
        )

        securityGroup = ec2.SecurityGroup.from_security_group_id(
            self, "task_security_group", security_group_id=security_group_name
        )

        ibcService = ecs.FargateService(
            self,
            "fargate_service",
            cluster=cluster,
            task_definition=task,
            assign_public_ip=False,
            desired_count=1,
            security_group=securityGroup,
            service_discovery_options=ecs.ServiceDiscoveryOptions(name=name),
            service_name=name,
            vpc_subnets=privateSubnets,
        )


app = cdk.App()
IBC(
    app,
    "ibc-live",
    "ibc-live",
    secrets_path="/ibc/live/",
    trading_mode="live",
    vpc_name="sandbox-VPC",
    security_group_name="sg-2cc6a145",
)
IBC(
    app,
    "ibc-paper",
    "ibc-paper",
    secrets_path="/ibc/paper/",
    trading_mode="paper",
    vpc_name="sandbox-VPC",
    security_group_name="sg-2cc6a145",
)
app.run()
