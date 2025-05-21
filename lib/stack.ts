import * as path from "node:path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { StackConfig } from "./types";
import { Playground } from "./playground";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";

const lambdaArchitecture = lambda.Architecture.X86_64;

/*
Tool request format: 
{
  "tool_use_id": "1234",
  "name": "stock-price",
  "input": {
    "ticker": "AMZN"
  }
}
*/

export interface ArtifactsAndToolsStackProps extends cdk.StackProps {
  config: StackConfig;
}

export class ArtifactsAndToolsStack extends cdk.Stack {
  constructor(
    scope: Construct,
    id: string,
    props: ArtifactsAndToolsStackProps
  ) {
    super(scope, id, {
      description: "Artifacts and Tools (uksb-l8wk3n27zh)",
      ...props,
    });

    const bedrockRegion = props.config.bedrockRegion ?? cdk.Aws.REGION;
    const bedrockModel = props.config.bedrockModel;
    const powerToolsLayerVersion = "72";
    const powerToolsLayer = lambda.LayerVersion.fromLayerVersionArn(
      this,
      "PowertoolsLayer",
      lambdaArchitecture === lambda.Architecture.X86_64
        ? `arn:${cdk.Aws.PARTITION}:lambda:${cdk.Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV2:${powerToolsLayerVersion}`
        : `arn:${cdk.Aws.PARTITION}:lambda:${cdk.Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:${powerToolsLayerVersion}`
    );

    const apiKeysSecret = new secretsmanager.Secret(this, "ApiKeysSecret", {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      secretObjectValue: {},
    });

    let codeInterpreterTool: lambda.IFunction | undefined;
    if (props.config.codeInterpreterTool?.enabled) {
      const codeInterpreterVpc = new ec2.Vpc(this, "CodeInterpreterVPC", {
        maxAzs: 2,
        natGateways: 0,
        createInternetGateway: false,
        subnetConfiguration: [
          {
            cidrMask: 24,
            name: "PrivateSubnet",
            subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          },
        ],
      });

      codeInterpreterVpc.addGatewayEndpoint("CodeInterpreterS3Endpoint", {
        service: ec2.GatewayVpcEndpointAwsService.S3,
      });

      const codeInterpreterLogGroup = new logs.LogGroup(
        this,
        "CodeInterpreterLogGroup",
        {
          retention: logs.RetentionDays.ONE_WEEK,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }
      );

      const codeInterpreterRole = new iam.Role(
        this,
        "CodeInterpreterExecutionRole",
        {
          assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
          inlinePolicies: {
            lambdaAccess: new iam.PolicyDocument({
              statements: [
                new iam.PolicyStatement({
                  effect: iam.Effect.ALLOW,
                  actions: [
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DescribeSubnets",
                    "ec2:DeleteNetworkInterface",
                    "ec2:AssignPrivateIpAddresses",
                    "ec2:UnassignPrivateIpAddresses",
                  ],
                  resources: ["*"],
                }),
                new iam.PolicyStatement({
                  effect: iam.Effect.ALLOW,
                  actions: ["logs:CreateLogStream", "logs:PutLogEvents"],
                  resources: [codeInterpreterLogGroup.logGroupArn],
                }),
                new iam.PolicyStatement({
                  effect: iam.Effect.ALLOW,
                  actions: ["s3:Get*", "s3:List*"],
                  resources: ["*"],
                }),
              ],
            }),
          },
        }
      );

      codeInterpreterTool = new lambda.DockerImageFunction(
        this,
        "CodeInterpreterTool",
        {
          code: lambda.DockerImageCode.fromImageAsset(
            path.join(__dirname, "./tools/code-interpreter")
          ),
          architecture: lambdaArchitecture,
          timeout: cdk.Duration.minutes(15),
          memorySize: 4096,
          logGroup: codeInterpreterLogGroup,
          vpc: codeInterpreterVpc,
          vpcSubnets: {
            subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          },
          role: codeInterpreterRole,
        }
      );

      new cdk.CfnOutput(this, "CodeInterpreterToolArn", {
        value: codeInterpreterTool.functionArn,
      });
    }

    let webSearchTool: lambda.IFunction | undefined;
    if (props.config.webSearchTool?.enabled) {
      const webSearchLogGroup = new logs.LogGroup(this, "WebSearchLogGroup", {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

      webSearchTool = new lambda.Function(this, "WebSearchTool", {
        architecture: lambdaArchitecture,
        timeout: cdk.Duration.minutes(15),
        memorySize: 2048,
        handler: "index.handler",
        logGroup: webSearchLogGroup,
        runtime: lambda.Runtime.NODEJS_20_X,
        code: lambda.Code.fromDockerBuild(
          path.join(__dirname, "./tools/web-search")
        ),
        environment: {
          API_KEYS_SECRET_ARN: apiKeysSecret.secretArn,
        },
      });

      apiKeysSecret.grantRead(webSearchTool);

      new cdk.CfnOutput(this, "WebSearchToolArn", {
        value: webSearchTool.functionArn,
      });
    }

    let athenaQueryTool: lambda.IFunction | undefined;
    if (props.config.athenaQueryTool?.enabled) {
      const athenaQueryLogGroup = new logs.LogGroup(
        this,
        "AthenaQueryLogGroup",
        {
          retention: logs.RetentionDays.ONE_WEEK,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }
      );

      athenaQueryTool = new lambda.DockerImageFunction(
        this,
        "AthenaQueryTool",
        {
          code: lambda.DockerImageCode.fromImageAsset(
            path.join(__dirname, "./tools/athena-query")
          ),
          architecture: lambdaArchitecture,
          timeout: cdk.Duration.minutes(5),
          memorySize: 128,
          logGroup: athenaQueryLogGroup,
          environment: {
            ATHENA_WORKGROUP:
              props.config.athenaQueryTool?.athenaWorkgroup || "",
          },
        }
      );

      // Grant permissions to the Athena query tool
      athenaQueryTool.addToRolePolicy(
        new iam.PolicyStatement({
          actions: [
            "athena:StartQueryExecution",
            "athena:GetQueryExecution",
            "athena:GetQueryResults",
            "athena:ListDatabases",
            "athena:GetDatabase",
            "athena:ListTableMetadata",
            "athena:GetTableMetadata",
            "athena:ListWorkgroups",
            "athena:ListDataCatalogs",
          ],
          resources: ["*"],
        })
      );

      athenaQueryTool.addToRolePolicy(
        new iam.PolicyStatement({
          actions: [
            "athena:GetWorkGroup",
            "athena:BatchGetQueryExecution",
            "athena:GetQueryExecution",
            "athena:ListQueryExecutions",
            "athena:StartQueryExecution",
            "athena:StopQueryExecution",
            "athena:GetQueryResults",
            "athena:GetQueryResultsStream",
            "athena:CreateNamedQuery",
            "athena:GetNamedQuery",
            "athena:BatchGetNamedQuery",
            "athena:ListNamedQueries",
            "athena:DeleteNamedQuery",
            "athena:CreatePreparedStatement",
            "athena:GetPreparedStatement",
            "athena:ListPreparedStatements",
            "athena:UpdatePreparedStatement",
            "athena:DeletePreparedStatement",
          ],
          resources: [
            `arn:aws:athena:eu-central-1:360749485620:workgroup/${props.config.athenaQueryTool?.athenaWorkgroup || "primary"}`,
          ],
        })
      );

      athenaQueryTool.addToRolePolicy(
        new iam.PolicyStatement({
          actions: ["s3:GetObject", "s3:ListBucket", "s3:GetBucketLocation"],
          resources: ["*"],
        })
      );

      athenaQueryTool.addToRolePolicy(
        new iam.PolicyStatement({
          actions: ["s3:PutObject"],
          resources: [
            `arn:aws:s3:::aws-athena-query-results-360749485620-eu-central-1/${props.config.athenaQueryTool?.athenaWorkgroup + "/" || ""}*`,
          ],
        })
      );

      athenaQueryTool.addToRolePolicy(
        new iam.PolicyStatement({
          actions: [
            "glue:GetDatabase",
            "glue:GetDatabases",
            "glue:GetTable",
            "glue:GetTables",
            "glue:GetPartitions",
            "glue:GetPartition",
          ],
          resources: ["*"],
        })
      );

      new cdk.CfnOutput(this, "AthenaQueryToolArn", {
        value: athenaQueryTool.functionArn,
      });
    }

    let databaseDocsTool: lambda.IFunction | undefined;
    if (props.config.databaseDocsTool?.enabled) {
      const databaseDocsLogGroup = new logs.LogGroup(this, "DatabaseDocsLogGroup", {
        retention: logs.RetentionDays.ONE_WEEK,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });
    
      databaseDocsTool = new lambda.Function(
        this,
        "DatabaseDocsTool",
        {
          runtime: lambda.Runtime.PYTHON_3_11, // or 3.13 if preferred
          handler: "index.handler", // points to your index.py file
          code: lambda.Code.fromAsset(
            path.join(__dirname, "./tools/database-docs")
          ),
          architecture: lambdaArchitecture,
          timeout: cdk.Duration.seconds(30), // Even shorter timeout since it's just docs
          memorySize: 256, // Can likely be even smaller (128MB)
          logGroup: databaseDocsLogGroup,
          environment: {
            // Add any environment variables if needed
          },
        }
      );
    
      new cdk.CfnOutput(this, "DatabaseDocsToolArn", {
        value: databaseDocsTool.functionArn,
      });
    }

    if (props.config.playground?.enabled) {
      const playground = new Playground(this, "Playground", {
        config: props.config,
        bedrockRegion,
        bedrockModel,
        lambdaArchitecture,
        powerToolsLayer,
        codeInterpreterTool,
        webSearchTool,
        athenaQueryTool,
        databaseDocsTool,
        athenaWorkgroup: props.config.athenaQueryTool?.athenaWorkgroup,
      });

      new cdk.CfnOutput(this, "CognitoUserPool", {
        value: `https://${
          cdk.Stack.of(this).region
        }.console.aws.amazon.com/cognito/v2/idp/user-pools/${
          playground.userPool.userPoolId
        }/users?region=${cdk.Stack.of(this).region}`,
      });

      new cdk.CfnOutput(this, "UserInterfaceDomainName", {
        value: `https://${playground.distribution.distributionDomainName}`,
      });
    }

    new cdk.CfnOutput(this, "ApiKeysSecretName", {
      value: apiKeysSecret.secretName,
    });
  }
}
