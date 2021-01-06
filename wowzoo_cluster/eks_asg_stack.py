from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
)


class EKSClusterWithASG(core.Stack):
    """
    Auto Scaling Group - EC2 worker nodes managed by the user.
    """

    def __init__(self, scope: core.Construct, construct_id: str,
                 eks_user: str, eks_key: str,
                 eks_vpc: ec2.Vpc, eks_security_group: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        eks_cluster = eks.Cluster(
            self,
            "EKSClusterWithASG",
            cluster_name="wowzoo-cluster-asg",
            version=eks.KubernetesVersion.V1_18,
            default_capacity=0,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            security_group=eks_security_group,
            vpc=eks_vpc,
        )

        eks_cluster.add_auto_scaling_group_capacity(
            "EKSAutoScaling",
            instance_type=ec2.InstanceType("t3.medium"),
            key_name=eks_key,
            max_capacity=10,
            min_capacity=1,
            auto_scaling_group_name="EKSAutoScaling",
            update_policy=autoscaling.UpdatePolicy.rolling_update(),
            allow_all_outbound=False,
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
