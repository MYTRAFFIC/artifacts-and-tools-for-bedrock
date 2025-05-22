deploy:
	uvx pre-commit run --files $$(git status -s | grep -E "^\s*[AM]" | awk '{print $2}') && \
	AWS_PROFILE=tech-admin npx cdk deploy
aws-logs:
	AWS_PROFILE=tech-admin aws logs tail /aws/lambda/ArtifactsAndTools-PlaygroundMessageHandlerE8F604BE-D09zvgXYsiUl --follow --since 10m
