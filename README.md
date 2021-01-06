# This is AWS CDK project creating AWS EKS Cluster 

- Auto Scaling Group - EC2 worker nodes managed by the user.
- Managed Node Group - EC2 worker nodes managed by EKS.
- Fargate Profile - Fargate worker nodes managed by EKS.

You need to set environment variables below

- export CDK_ACCOUNT=xxxxxxx
  - AWS Account number
- export CDK_REGION=xxxxxxx
  - AWS Region
- export EKS_USER=xxxxxxx
  - AWS IAM username
- export EKS_KEY=xxxxxxx
  - AWS EC2 Key pair name
- export AUTOSCALER_VER=xxxxxxx
  - Cluster Autoscaler version
- export AUTOSCALER_MANIFEST_URL=xxxxxxx
  - Cluster Autoscaler manifest url