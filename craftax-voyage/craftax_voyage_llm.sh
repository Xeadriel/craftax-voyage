#!/bin/bash
#SBATCH --job-name=craftax-voyage
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=/home/oasik/craftax-voyage/logs/%j.out
#SBATCH --error=/home/oasik/craftax-voyage/logs/%j.err

cd ~oasik/craftax-voyage/

# rm -rf .venv

# uv python install 3.12 

# uv venv --python 3.12 --managed-python
source .venv/bin/activate

# uv pip install -e craftax-voyage
# uv pip install --upgrade transformers
# uv pip install "vllm>=0.17"

cd craftax-voyage

#vllm serve Qwen/Qwen3.5-9B > logs/${SLURM_JOB_ID}_vllm.log 2>&1 &
#vllm serve Qwen/Qwen3.5-9B --tensor-parallel-size 2 > logs/${SLURM_JOB_ID}_vllm.log 2>&1 &
vllm serve Qwen/Qwen3.5-4B --port 8000 > logs/${SLURM_JOB_ID}_vllm.log 2>&1 &

wait