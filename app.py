#!/usr/bin/env python3

import os

from aws_cdk import core
from wowzoo_cluster.eks_vpc_stack import EKSClusterVPC
from wowzoo_cluster.eks_asg_stack import EKSClusterWithASG
from wowzoo_cluster.eks_ng_stack import EKSClusterWithNG
from wowzoo_cluster.eks_fargate_stack import EKSClusterWithFargate


app = core.App()

account = os.environ["CDK_ACCOUNT"]
region = os.environ["CDK_REGION"]
user = os.environ["EKS_USER"]
key = os.environ["EKS_KEY"]

eks_cluster_vpc = EKSClusterVPC(
    app,
    "EKSCluster",
    env={"account": account, "region": region}
)

EKSClusterWithASG(
    app,
    "EKSClusterWithASG",
    eks_user=user,
    eks_key=key,
    eks_vpc=eks_cluster_vpc.vpc,
    eks_security_group=eks_cluster_vpc.security_group,
    env={"account": account, "region": region}
)

EKSClusterWithNG(
    app,
    "EKSClusterWithNG",
    eks_user=user,
    eks_key=key,
    eks_vpc=eks_cluster_vpc.vpc,
    eks_security_group=eks_cluster_vpc.security_group,
    env={"account": account, "region": region}
)

EKSClusterWithFargate(
    app,
    "EKSClusterWithFargate",
    eks_user=user,
    eks_vpc=eks_cluster_vpc.vpc,
    eks_security_group=eks_cluster_vpc.security_group,
    env={"account": account, "region": region}
)

core.Tags.of(app).add("Owner", user)

app.synth()
