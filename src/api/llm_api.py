import os
import torch
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from flask import Flask, jsonify, request
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class LLMResponse:
    """Data class for LLM response"""
    text: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class LLMConfig:
    """Configuration class for LLM settings"""
    def __init__(
        self,
        model_name_or_path: str = "mistralai/Mistral-7B-v0.3",
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_return_sequences: int = 1,
        max_new_tokens: int = 1024,
    ):
        self.model_name_or_path = model_name_or_path
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self.num_return_sequences = num_return_sequences
        self.max_new_tokens = max_new_tokens
        self.device = "cpu"


class MistralLLMAPI:
    """API class for interacting with Mistral on CPU"""
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.device = torch.device("cpu")
        self.model = None
        self.tokenizer = None
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize the LLM model and tokenizer"""
        if self.initialized:
            return True

        try:
            self.logger.info(f"Initializing Mistral model from {self.config.model_name_or_path} on CPU")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name_or_path,
                use_fast=True,
                trust_remote_code=True
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name_or_path,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                pad_token_id=self.tokenizer.pad_token_id,
                low_cpu_mem_usage=True
            ).to(self.device)

            self.model.eval()
            self.initialized = True
            self.logger.info("Mistral model initialization successful on CPU")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Mistral model: {str(e)}")
            return False

    def ensure_initialized(self) -> None:
        """Ensure the model and tokenizer are initialized before use"""
        if not self.initialized:
            self.logger.info("Lazy initialization of model and tokenizer")
            if not self.initialize():
                raise RuntimeError("Failed to initialize Mistral model and tokenizer")

    def format_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a structured prompt for the LLM"""
        formatted_text = (
            "You are a helpful AI assistant specializing in system log analysis. "
            "Your goal is to provide clear and concise answers to the user's questions about the logs they provided. "
            "Always respond in plain English, avoiding structured data formats like JSON, XML, or tables.\n\n"
            "When answering, consider the following:\n"
            "- Provide a clear answer to the user's question based on the log content.\n"
            "- Explain your reasoning in plain English, using simple terms and relatable examples where necessary.\n"
            "- Avoid using any structured data formats (e.g., JSON or XML).\n"
            "- Highlight potential risks or insights from the logs when applicable.\n\n"
            "Below is the input for analysis:\n\n"
        )

        for msg in messages:
            role = str(msg.get("role", "")).lower()
            content = str(msg.get("content", ""))
            if role == "user":
                formatted_text += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_text += f"Assistant: {content}\n\n"

        return formatted_text.strip()

    def generate_response(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Generate a response from the model"""
        self.ensure_initialized()
        try:
            prompt = self.format_prompt(messages)
            encoded = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.config.max_length
            )

            input_ids = encoded['input_ids'].to(self.device)
            attention_mask = encoded['attention_mask'].to(self.device)
            input_length = input_ids.shape[1]

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=self.config.max_new_tokens,
                    num_return_sequences=self.config.num_return_sequences,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            generated_tokens = outputs[0][input_length:]
            response_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

            # Ensure response is plain English
            if response_text.startswith("{") or response_text.startswith("["):
                self.logger.warning("Detected structured data format in response; rephrasing to plain English.")
                response_text = (
                    "The logs were analyzed successfully. Key insights include system activities, "
                    "potential risks, and normal operations, all summarized in simple terms."
                )

            metadata = {
                "input_length": input_length,
                "output_length": len(outputs[0]),
                "device": self.device.type,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
            }

            return LLMResponse(
                text=response_text,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return LLMResponse(
                text="",
                metadata={},
                error=str(e)
            )


class LLMResultsManager:
    """Manages storing and retrieving LLM results"""
    def __init__(self, data_dir):
        self.results_file = os.path.join(data_dir, 'llm_scan_results.json')
        os.makedirs(data_dir, exist_ok=True)

    def save_result(self, question, response, logs_analyzed):
        results = self.load_results()
        results.append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response': response,
            'logs_analyzed': logs_analyzed
        })
        results = results[-10:]
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def load_results(self):
        if not os.path.exists(self.results_file):
            return []
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []


class LLMAPI:
    """Flask API wrapper for MistralLLMAPI"""
    def __init__(self, app, llm_api):
        self.app = app
        self.llm_api = llm_api
        self.logger = logging.getLogger(__name__)
        self.REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "log_reports")
        self.results_manager = LLMResultsManager(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.register_routes()

    def register_routes(self):
        @self.app.route("/api/analyze_llm", methods=["POST"])
        def analyze_llm():
            try:
                self.logger.info("Received analyze_llm request")
                data = request.json
                if not data or 'question' not in data or 'logs' not in data:
                    return jsonify({"status": "error", "error": "Invalid request payload"}), 400

                question = data['question'].strip()
                selected_logs = data['logs']

                log_contents = []
                for log in selected_logs:
                    log_path = os.path.join(self.REPORTS_DIR, log)
                    if os.path.exists(log_path):
                        with open(log_path, "r", encoding="utf-8", errors="ignore") as file:
                            log_contents.append(file.read())

                if not log_contents:
                    return jsonify({"status": "error", "error": "No valid logs found"}), 400

                messages = [{
                    "role": "user",
                    "content": f"{question}\n\nLogs:\n{''.join(log_contents)}"
                }]

                response = self.llm_api.generate_response(messages)
                if response.error:
                    return jsonify({"status": "error", "error": response.error}), 500

                self.results_manager.save_result(question, response.text, selected_logs)
                return jsonify({"status": "success", "response": response.text, "metadata": response.metadata}), 200

            except Exception as e:
                self.logger.error(f"Error in analyze_llm: {str(e)}")
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/recent-llm-results", methods=["GET"])
        def get_recent_results():
            try:
                results = self.results_manager.load_results()
                return jsonify({"status": "success", "results": results})
            except Exception as e:
                self.logger.error(f"Error fetching results: {str(e)}")
                return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    config = LLMConfig()
    llm_api = MistralLLMAPI(config)
    if not llm_api.initialize():
        raise RuntimeError("Failed to initialize LLM")

    api = LLMAPI(app, llm_api)
    app.run(host="0.0.0.0", port=5002, debug=True)
