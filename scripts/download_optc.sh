#!/bin/bash

# This script downloads the DARPA OPTC dataset from its public S3 bucket
# Zeek logs size: ~50GB
# See: https://github.com/FiveDirections/OPTC-Data-Evaluation

echo "Starting download of DARPA OPTC dataset..."
# TODO: Add curl/wget commands for the specific S3 buckets/files
# e.g., wget https://optc.s3.amazonaws.com/zeek_logs.tar.gz

echo "Extracting logs..."
# TODO: Add extraction commands

echo "Download and extraction complete. Logs saved to data/raw/"
