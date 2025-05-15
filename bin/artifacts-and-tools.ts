#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { StackConfig } from "../lib/types";
import { ArtifactsAndToolsStack } from "../lib/stack";

const config: StackConfig = {
  bedrockRegion: "eu-central-1",
  bedrockModel: "eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
  playground: {
    enabled: true,
  },
  artifacts: {
    enabled: true,
  },
  codeInterpreterTool: {
    enabled: true,
  },
  webSearchTool: {
    enabled: true,
  },
  athenaQueryTool: {
    enabled: true,
    resultsLocation: "s3://YOUR_BUCKET_NAME/athena-results/", // Replace with your actual S3 bucket for Athena query results
  },
};

const app = new cdk.App();
new ArtifactsAndToolsStack(app, "ArtifactsAndTools", { config });
