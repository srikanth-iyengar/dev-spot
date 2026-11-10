#!/bin/bash

set -e

root_dir=$(pwd)

## Get the target cloudformation bucket
cloudformation_bucket=$(aws resourcegroupstaggingapi get-resources \
		--resource-type-filters "s3:bucket" \
		--tag-filters "Key=Purpose,Values=Dev-Spot" \
		--query "ResourceTagMappingList[].ResourceARN" \
		--output text)

bucket_name=${cloudformation_bucket#arn:aws:s3:::}

## Create the bucket if it doesn't exists
if [ -z "$bucket_name" ]; then
	echo "Dev Spot needs a S3 bucket to push the lambda and cloudformation templates required"
	read -p "Enter the region for the dev-spot bucket: " region
	echo $region

	read -p "Enter a bucket name: " bucket

	aws s3 mb s3://$bucket --region $region
	aws s3api put-bucket-tagging --bucket $bucket --region $region --tagging 'TagSet=[{Key=Purpose,Value=Dev-Spot}]'
	bucket_name=$bucket
fi

## Build the discord bot lambda
cd $root_dir/bot

if [ ! -d "venv" ]; then
	echo "Venv not found"
	python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -t package

./build.sh

cd $root_dir

mkdir -p build
mkdir -p build/cloudformation
mkdir -p build/lambda

cp $root_dir/deploy/spot-base-wrapper/product.template.yaml $root_dir/build/cloudformation/product.base.yaml
cp $root_dir/bot/deploy.zip $root_dir/build/lambda
cp $root_dir/deploy/instance-stack/product.template.yaml $root_dir/build/cloudformation/instance-stack.template.yaml

aws s3 sync ./build s3://$bucket_name

set_param() {
	local result=$(echo $1 | jq --arg key "$2" --arg val "$3" 'map(if .ParameterKey == $key then .ParameterValue = $val else . end)')
	echo $result
}

if [ ! -f "$root_dir/build/parameters.json" ]; then
	parameter_template=$(cat $root_dir/deploy/spot-base-wrapper/parameter.template.json)

	read -p "Enter EBS persistence storage you need: " ebsSize
	read -p "Enter aws az you want your instance to be placed: " az
	read -p "Enter the discord channel webhook url: " webhookUrl
	read -p "Enter discord bot pubkey: " botPubKey
	read -p "Enter EC2 image id: " ami
	read -p "Enter the instance type you intend to use: " instanceType
	read -p "Bootstrap script path: " initScriptPath

	params=$parameter_template
	params=$(set_param "$params" "PersistenceEbsSize" "$ebsSize")
	params=$(set_param "$params" "az" "$az")
	params=$(set_param "$params" "BotPubKey" "$botPubKey")
	params=$(set_param "$params" "SourceS3Bucket" "$bucket_name")
	params=$(set_param "$params" "DiscordPushWebhookUrl" "$webhookUrl")
	params=$(set_param "$params" "ImageId" "$ami")
	params=$(set_param "$params" "InstanceType" "$instanceType")
	params=$(set_param "$params" "BootstrapScript" "$(cat $initScriptPath)")

	echo $params > $root_dir/build/parameters.json
fi

