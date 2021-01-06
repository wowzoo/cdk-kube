from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
)


class EKSClusterWithFargate(core.Stack):
    """
    Fargate Profile - Fargate worker nodes managed by EKS.
    """

    def __init__(self, scope: core.Construct, construct_id: str,
                 eks_user: str,
                 eks_vpc: ec2.Vpc, eks_security_group: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        eks_cluster = eks.FargateCluster(
            self,
            "EKSClusterWithFargate",
            cluster_name="wowzoo-cluster-fargate",
            version=eks.KubernetesVersion.V1_18,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            security_group=eks_security_group,
            vpc=eks_vpc,
        )

        eks_cluster_user = iam.User.from_user_name(
            self,
            "EKSClusterUser",
            user_name=eks_user
        )

        eks_cluster.aws_auth.add_user_mapping(
            eks_cluster_user,
            groups=["system:masters"]
        )
