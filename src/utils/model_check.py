# src/utils/model_check.py
import os
import torch
from transformers import AutoConfig, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_model_setup(model_path: str):
    """Verify model files and configuration"""
    logger.info(f"Checking model setup in: {model_path}")
    
    # Check required files
    required_files = ['config.json', 'tokenizer.model', 'tokenizer_config.json', 'pytorch_model.bin']
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
            logger.error(f"Missing required file: {file}")
        else:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            logger.info(f"Found {file}: {file_size:.2f} MB")

    if missing_files:
        logger.error("Model setup incomplete. Missing files: " + ", ".join(missing_files))
        return False

    try:
        # Check config
        config = AutoConfig.from_pretrained(model_path)
        logger.info("Model configuration:")
        logger.info(f"Hidden size: {config.hidden_size}")
        logger.info(f"Num layers: {config.num_hidden_layers}")
        logger.info(f"Num attention heads: {config.num_attention_heads}")
        
        # Check tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info(f"Vocabulary size: {tokenizer.vocab_size}")
        logger.info(f"Model max length: {tokenizer.model_max_length}")
        
        # Check CUDA availability
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

        return True

    except Exception as e:
        logger.error(f"Error checking model setup: {str(e)}")
        return False

if __name__ == "__main__":
    # Use your actual model path
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "models", "MobileLLM", "configs", "1.5B")
    check_model_setup(MODEL_PATH)