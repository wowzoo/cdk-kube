import yaml
import requests
import os

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
)


class EKSClusterWithNG(core.Stack):
    """
    Managed Node Group - EC2 worker nodes managed by EKS.
    """

    def __init__(self, scope: core.Construct, construct_id: str,
                 eks_user: str, eks_key: str,
                 eks_vpc: ec2.Vpc, eks_security_group: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._eks_cluster = eks.Cluster(
            self,
            "EKSClusterWithNG",
            cluster_name="wowzoo-cluster-ng",
            version=eks.KubernetesVersion.V1_18,
            default_capacity=0,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            security_group=eks_security_group,
            vpc=eks_vpc,
        )

        self._eks_ng = self._eks_cluster.add_nodegroup_capacity(
            "EKSNodeGroup",
            nodegroup_name="EKSNodeGroup",
            capacity_type=eks.CapacityType.ON_DEMAND,
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=1,
            max_size=5,
            remote_access=eks.NodegroupRemoteAccess(ssh_key_name=eks_key),
            tags={"Owner": eks_user}
        )

        eks_cluster_user = iam.User.from_user_name(
            self,
            "EKSClusterUser",
            user_name=eks_user
        )

        self._eks_cluster.aws_auth.add_user_mapping(
            eks_cluster_user,
            groups=["system:masters"]
        )

        core.CfnOutput(
            self,
            "OIDC URL",
            value=self._eks_cluster.cluster_open_id_connect_issuer_url
        )

        autoscaler_role = self._set_cluster_autoscaler_role()

        manifest = self._get_manifest(autoscaler_role)
        self._eks_cluster.add_manifest(
            "ClusterAutoScaler",
            *manifest
        )

    def _set_cluster_autoscaler_role(self) -> iam.Role:
        provider = eks.OpenIdConnectProvider(
            self,
            "EKSClusterOIDCProvider",
            url=self._eks_cluster.cluster_open_id_connect_issuer_url
        )

        principal_condition = core.CfnJson(
            self,
            "PrincipalCondition",
            value={
                f"{provider.open_id_connect_provider_issuer}:sub": "system:serviceaccount:kube-system:cluster-autoscaler"
            }
        )

        autoscaler_principal = iam.WebIdentityPrincipal(
            provider.open_id_connect_provider_arn
        ).with_conditions(
            {
                "StringEquals": principal_condition
            }
        )

        autoscaler_role = iam.Role(
            self,
            "EKSClusterAutoScalerRole",
            role_name="EKSClusterAutoScalerRole",
            assumed_by=autoscaler_principal,
            description="Role for EKS Cluster AutoScaler",
        )

        autoscaler_stmt = iam.PolicyStatement(
            resources=["*"],
            actions=[
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "ec2:DescribeLaunchTemplateVersions"
            ],
            effect=iam.Effect.ALLOW
        )

        autoscaler_policy = iam.Policy(
            self,
            "EKSClusterAutoScalerPolicy",
            policy_name="EKSClusterAutoScalerPolicy",
            statements=[autoscaler_stmt],
        )

        autoscaler_policy.attach_to_role(autoscaler_role)

        return autoscaler_role

    def _get_manifest(self, autoscaler_role: iam.Role) -> list:
        autoscaler_ver = os.environ["AUTOSCALER_VER"]
        manifest_url = os.environ["AUTOSCALER_MANIFEST_URL"]
        manifest_yaml = requests.get(manifest_url)

        manifest = list(yaml.safe_load_all(manifest_yaml.content))
        deployment_done = False
        serviceaccount_done = False
        for m in manifest:
            if m["kind"] == "Deployment":
                if deployment_done:
                    raise Exception("More than one Deployment")

                annotations = m["spec"]["template"]["metadata"]["annotations"]
                annotations["cluster-autoscaler.kubernetes.io/safe-to-evict"] = "false"

                container = m["spec"]["template"]["spec"]["containers"][0]
                image = container["image"]
                uri, ver = image.split(":")
                if ver != autoscaler_ver:
                    container["image"] = f"{uri}:{autoscaler_ver}"

                commands = container["command"]
                for i, com in enumerate(commands):
                    if "<YOUR CLUSTER NAME>" in com:
                        commands[i] = com.replace("<YOUR CLUSTER NAME>", self._eks_cluster.cluster_name, 1)
                        break
                else:
                    raise Exception("No <YOUR CLUSTER NAME>")

                commands.append("--balance-similar-node-groups")
                commands.append("--skip-nodes-with-system-pods=false")

                deployment_done = True

            elif m["kind"] == "ServiceAccount":
                if serviceaccount_done:
                    raise Exception("More than one ServiceAccount")

                m["metadata"]["annotations"] = {
                    "eks.amazonaws.com/role-arn": autoscaler_role.role_arn
                }

                serviceaccount_done = True

                print(m)

        if not deployment_done:
            raise Exception("No Deployment Section in manifest")

        if not serviceaccount_done:
            raise Exception("No ServiceAccount Section in manifest")

        return manifest
