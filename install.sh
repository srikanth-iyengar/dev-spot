#!/bin/bash

set -e

## Get the target cloudformation bucket
cloudformation_bucket=$(aws resourcegroupstaggingapi get-resources \
		--resource-type-filters "s3:bucket" \
		--tag-filters "Key=Purpose,Values=Dev-Spot" \
		--query "ResourceTagMappingList[].ResourceARN" \
		--output text)

bucket_name=${cloudformation_bucket#arn:aws:s3:::}

if [ -z "$bucket_name" ]; then
	echo "!!!No dev spot bucket found, initalize the bucket using init.sh"
	exit 1
fi


