from typing import Tuple

import torch
from transformers import BartForConditionalGeneration, AutoTokenizer

from settings import DEFAULT_MODEL_NAME, logger


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SummaryModel(metaclass=Singleton):
    def __init__(self, model_name, max_tokens=1024):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.model, self.tokenizer = self.load_model()

    @staticmethod
    def get_model_args():
        return {
            "num_beams": 3,
            "min_length": 60,
            "max_length": 200,
            "early_stopping": True,
        }

    @staticmethod
    def get_tokenizer_args():
        return {
            "skip_special_tokens": True,
            "clean_up_tokenization_spaces": False,
        }

    def load_model(self):
        logger.info(f"Loading the summarization model {self.model_name}")
        model = BartForConditionalGeneration.from_pretrained(self.model_name)
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model.eval()
        return model, tokenizer

    async def prepare_batch(
        self, content, message
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        inputs = self.tokenizer.encode_plus(
            content, return_tensors="pt", add_special_tokens=False
        )
        input_id_chunks = list(inputs["input_ids"][0].split(self.max_tokens))
        num_parts = len(input_id_chunks)
        num_chunks = len(input_id_chunks)

        if message:
            logger.info(f"Splitting the article into {num_parts} parts")
            await message.reply(f"Splitting the article into {num_parts} parts...")
        # we want to process the last chunk separately and do not pad it since it leads to poor results
        if num_chunks == 1:
            return input_id_chunks[0].unsqueeze(0), torch.tensor([])
        elif num_chunks > 1:
            chunks = torch.stack(input_id_chunks[:-1]) if len(input_id_chunks) > 1 else input_id_chunks[0].unsqueeze(0)
            last_chunk = input_id_chunks[-1].unsqueeze(0)
            return chunks, last_chunk
        else:
            raise ValueError("Text is too short for processing")

    def get_summary(self, batches: Tuple[torch.Tensor, torch.Tensor]):
        result = []
        for batch in batches:
            summary_encoded = self.model.generate(batch, **self.get_model_args())
            summary = self.tokenizer.batch_decode(
                summary_encoded, **self.get_tokenizer_args()
            )
            result.extend(summary)
        return result


def _prettify_one(line: str) -> str:
    if line.startswith("."):
        line = line[1:]
    return line.strip()


def prettify(items) -> str:
    message_text = ""
    for item in items:
        message_text += f"• {_prettify_one(item)}\n\n"
    return message_text


async def summarize_article(
    content: str, message=None, model_name=DEFAULT_MODEL_NAME
) -> str:
    """
    Summarize the article with Hugging Face's model
    """
    try:
        if not content:
            raise ValueError("No content to summarize")
            
        model = SummaryModel(model_name)
        batches = await model.prepare_batch(content, message)
        
        # Проверяем второй элемент батча
        if isinstance(batches[1], torch.Tensor) and batches[1].nelement() == 0:
            # Обрабатываем как один чанк
            content_summaries = model.get_summary((batches[0], batches[0]))
        else:
            content_summaries = model.get_summary(batches)
            
        if not content_summaries:
            return ["Could not generate summary for the provided content"]
            
        
        logger.info(f"\ncontent_summaries:\n {content_summaries}\n")
        return prettify(content_summaries)
        
    except ValueError as e:
        logger.error(f"Value error in summarization: {str(e)}")
        return [f"Error: {str(e)}"]
    except RuntimeError as e:
        logger.error(f"Runtime error in summarization: {str(e)}")
        return ["Error processing the text. The content might be too short or empty."]
    except Exception as e:
        logger.error(f"Unexpected error in summarization: {str(e)}")
        return ["An unexpected error occurred while processing the text."]
