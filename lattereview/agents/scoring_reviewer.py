"""Reviewer agent implementation with consistent error handling and type safety."""

import asyncio
from pathlib import Path
import datetime
from typing import List, Dict, Any, Optional, Callable
from pydantic import Field
from .base_agent import BaseAgent, AgentError, ReasoningType
from tqdm.asyncio import tqdm
import warnings

DEFAULT_MAX_RETRIES = 3


class ScoringReviewer(BaseAgent):
    response_format: Dict[str, Any] = {"reasoning": str, "score": int, "certainty": int}
    scoring_task: Optional[str] = None
    scoring_set: List[int] = [1, 2]
    scoring_rules: str = "Your scores should follow the defined schema."
    generic_prompt: Optional[str] = Field(default=None)
    input_description: str = "article title/abstract"
    reasoning: ReasoningType = ReasoningType.BRIEF
    max_retries: int = DEFAULT_MAX_RETRIES

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any) -> None:
        """Initialize after Pydantic model initialization."""
        try:
            assert self.reasoning != ReasoningType.NONE, "Reasoning type cannot be 'none' for ScoringReviewer"
            prompt_path = Path(__file__).parent.parent / "generic_prompts" / "scoring_review_prompt.txt"
            if not prompt_path.exists():
                raise FileNotFoundError(f"Review prompt template not found at {prompt_path}")
            self.generic_prompt = prompt_path.read_text(encoding="utf-8")
            self.setup()
        except Exception as e:
            raise AgentError(f"Error initializing agent: {str(e)}")

    def setup(self) -> None:
        """Build the agent's identity and configure the provider."""
        try:
            self.system_prompt = self._build_system_prompt()
            self.scoring_set = str(self.scoring_set)
            keys_to_replace = ["scoring_task", "scoring_set", "scoring_rules", "reasoning", "examples"]

            self.formatted_prompt = self._process_prompt(
                self.generic_prompt, {key: getattr(self, key) for key in keys_to_replace}
            )

            self.identity = {
                "system_prompt": self.system_prompt,
                "formatted_prompt": self.formatted_prompt,
                "model_args": self.model_args,
            }

            if not self.provider:
                raise AgentError("Provider not initialized")

            self.provider.set_response_format(self.response_format)
            self.provider.system_prompt = self.system_prompt
        except Exception as e:
            raise AgentError(f"Error in setup: {str(e)}")

    async def review_items(
        self, text_input_strings: List[str], image_path_lists: List[List[str]] = None, tqdm_keywords: dict = None
    ) -> List[Dict[str, Any]]:
        """Review a list of items asynchronously with concurrency control and progress bar."""
        try:
            self.setup()
            if not image_path_lists:
                image_path_lists = [[]] * len(text_input_strings)
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)

            async def limited_review_item(
                text_input_string: str, image_path_list: List[str], index: int
            ) -> tuple[int, Dict[str, Any], Dict[str, float]]:
                async with semaphore:
                    response, input_prompt, cost = await self.review_item(text_input_string, image_path_list)
                    return index, response, input_prompt, cost

            # Building the tqdm desc
            if tqdm_keywords:
                tqdm_desc = f"""{[f'{k}: {v}' for k, v in tqdm_keywords.items()]} - \
                    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            else:
                tqdm_desc = f"Reviewing {len(text_input_strings)} items - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Create tasks with indices
            tasks = [
                limited_review_item(text_input_string, image_path_list, i)
                for i, (text_input_string, image_path_list) in enumerate(zip(text_input_strings, image_path_lists))
            ]

            # Collect results with indices
            initial_results = []
            async for result in tqdm(asyncio.as_completed(tasks), total=len(text_input_strings), desc=tqdm_desc):
                initial_results.append(await result)

            # Sort by original index and separate response and cost
            initial_results.sort(key=lambda x: x[0])  # Sort by index
            results = []

            for i, response, input_prompt, cost in initial_results:
                if isinstance(cost, dict):
                    cost = cost["total_cost"]
                self.cost_so_far += cost
                results.append(response)
                self.memory.append(
                    {
                        "system_prompt": self.system_prompt,
                        "model_args": self.model_args,
                        "input_prompt": input_prompt,
                        "response": response,
                        "cost": cost,
                    }
                )

            return results, cost
        except Exception as e:
            raise AgentError(f"Error reviewing items: {str(e)}")

    async def review_item(
        self, text_input_string: str, image_path_list: List[str] = []
    ) -> tuple[Dict[str, Any], Dict[str, float]]:
        """Review a single item asynchronously with error handling."""
        num_tried = 0
        while num_tried < self.max_retries:
            try:
                input_prompt = self._process_prompt(self.formatted_prompt, {"item": text_input_string})
                if self.additional_context == "":
                    context = self.additional_context
                elif isinstance(self.additional_context, str):
                    context = self._process_additional_context(self.additional_context)
                elif isinstance(self.additional_context, Callable):
                    context = await self.additional_context(text_input_string)
                    context = self._process_additional_context(context)
                else:
                    raise AgentError("Additional context must be a string or callable")
                input_prompt = self._process_prompt(input_prompt, {"additional_context": context})
                response, cost = await self.provider.get_json_response(input_prompt, image_path_list, **self.model_args)
                return response, input_prompt, cost
            except Exception as e:
                warnings.warn(f"Error reviewing item: {str(e)}. Retrying {num_tried}/{self.max_retries}")
        raise AgentError("Error reviewing item!")
