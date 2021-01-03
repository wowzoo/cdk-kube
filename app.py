#!/usr/bin/env python3

from aws_cdk import core

from wowzoo_cluster.wowzoo_cluster_stack import WowzooClusterStack


app = core.App()
WowzooClusterStack(app, "wowzoo-cluster")

app.synth()
