from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ssm as ssm,
)


class EKSClusterVPC(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._eks_vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,
            cidr="10.100.0.0/16",
            # Create 2 groups in 2 AZs
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE,
                    name="Private",
                    cidr_mask=24
                )
            ],
            nat_gateways=2,
        )

        ssm.StringParameter(
            self,
            "EKSVPCIDStringParameter",
            parameter_name="eks-vpc-id",
            string_value=self._eks_vpc.vpc_id
        )

        self._eks_security_group = ec2.SecurityGroup(
            self,
            "EKSClusterSecurityGroup",
            vpc=self._eks_vpc,
            description="Security Group for EKS Cluster",
            security_group_name="EKSClusterSecurityGroup",
            allow_all_outbound=False
        )

        ssm.StringParameter(
            self,
            "EKSSecurityGroupStringParameter",
            parameter_name="eks-security-group-id",
            string_value=self._eks_security_group.security_group_id
        )

        core.CfnOutput(
            self,
            "VPC ID",
            value=self._eks_vpc.vpc_id
        )

        core.CfnOutput(
            self,
            "Security Group ID",
            value=self._eks_security_group.security_group_id
        )

    @property
    def vpc(self):
        return self._eks_vpc

    @property
    def security_group(self):
        return self._eks_security_group
