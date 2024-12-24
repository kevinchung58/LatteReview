import pydantic
from typing import List, Dict, Any, Union
import pandas as pd
import json
import hashlib

from ..agents.scoring_reviewer import ScoringReviewer


class ReviewWorkflowError(Exception):
    """Base exception for workflow-related errors."""

    pass


class ReviewWorkflow(pydantic.BaseModel):
    workflow_schema: List[Dict[str, Any]] 
    memory: List[Dict] = list()
    reviewer_costs: Dict = dict()
    total_cost: float = 0.0
    verbose: bool = True

    def __post_init__(self, __context):
        """Initialize after Pydantic model initialization."""
        try:
            for review_task in self.workflow_schema:
                # Validate reviewers
                reviewers = (
                    review_task["reviewers"]
                    if isinstance(review_task["reviewers"], list)
                    else [review_task["reviewers"]]
                )
                for reviewer in reviewers:
                    if not isinstance(reviewer, ScoringReviewer):
                        raise ReviewWorkflowError(f"Invalid reviewer: {reviewer}")

                # Validate text_input columns
                text_inputs = review_task["text_inputs"] if isinstance(review_task["text_inputs"], list) else [review_task["text_inputs"]]
                for text_input in text_inputs:
                    if text_input not in __context["data"].columns:
                        reviewer_name = text_input.split("_")[1]
                        reviewer = next(reviewer for reviewer in reviewers if reviewer.name == reviewer_name)
                        assert reviewer is not None, f"Reviewer {reviewer_name} not found in provided inputs"
                        response_keywords = reviewer.response_format.keys() # e.g., ["_output", "_score", "_reasoning", "_certainty"]
                        assert text_input.split("_")[-1] in response_keywords, f"Invalid input: {text_input}"
        except Exception as e:
            raise ReviewWorkflowError(f"Error initializing Review Workflow: {e}")

    async def __call__(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> pd.DataFrame:
        """Run the workflow."""
        try:
            if isinstance(data, pd.DataFrame):
                return await self.run(data)
            elif isinstance(data, dict):
                return await self.run(pd.DataFrame(data))
            else:
                raise ReviewWorkflowError(f"Invalid data type: {type(data)}")
        except Exception as e:
            raise ReviewWorkflowError(f"Error running workflow: {e}")

    def _create_text_hash(self, content: str) -> str:
        """Create a hash of the content for tracking."""
        return hashlib.md5(content.encode()).hexdigest()

    def _format_text_input(self, row: pd.Series, text_inputs: List[str]) -> tuple:
        """Format input text with content tracking."""
        parts = []
        content_keys = []

        for text_input in text_inputs:
            value = str(row[text_input]).strip()
            parts.append(f"=== {text_input} ===\n{value}")
            content_keys.append(self._create_text_hash(value))

        return "\n\n".join(parts), "-".join(content_keys)

    async def run(self, data: pd.DataFrame) -> pd.DataFrame:
        """Run the review process with content validation."""
        try:
            df = data.copy()
            total_rounds = len(self.workflow_schema)

            for review_round, review_task in enumerate(self.workflow_schema):
                round_id = review_task["round"]
                self._log(f"\n====== Starting review round {round_id} ({review_round + 1}/{total_rounds}) ======\n")

                reviewers = (
                    review_task["reviewers"]
                    if isinstance(review_task["reviewers"], list)
                    else [review_task["reviewers"]]
                )
                text_inputs = review_task["text_inputs"] if isinstance(review_task["text_inputs"], list) else [review_task["text_inputs"]]
                filter_func = review_task.get("filter", lambda x: True)

                # Apply filter and get eligible rows
                mask = df.apply(filter_func, axis=1)
                if not mask.any():
                    self._log(f"Skipping review round {round_id} - no eligible rows")
                    continue

                self._log(f"Processing {mask.sum()} eligible rows")

                # Create input items with content tracking
                text_input_items = []
                text_input_hashes = []
                eligible_indices = []

                for idx in df[mask].index:
                    row = df.loc[idx]
                    text_input, text_hash = self._format_text_input(row, text_inputs)

                    # Add metadata header
                    text_input = (
                        f"Review Task ID: {round_id}-{idx}\n" f"Content Hash: {text_hash}\n\n" f"{text_input}"
                    )

                    text_input_items.append(text_input)
                    text_input_hashes.append(text_hash)
                    eligible_indices.append(idx)

                # Process each reviewer
                for reviewer in reviewers:
                    response_keywords = reviewer.response_format.keys()
                    response_cols = [f"round-{round_id}_{reviewer.name}_{keyword}" for keyword in response_keywords]
                    output_col = f"round-{round_id}_{reviewer.name}_output"

                    # Initialize the output column and all expected response columns if they don't exist
                    # The output column is the entire output from the reviewer, while the response columns are specific

                    if output_col not in df.columns:
                        df[output_col] = None

                    for response_col in response_cols:
                        if response_col not in df.columns:
                            df[response_col] = None

                    # Get reviewer outputs with metadata
                    outputs, review_cost = await reviewer.review_items(
                        text_input_items,
                        {
                            "round": round_id,
                            "reviewer_name": reviewer.name,
                        },
                    )
                    self.reviewer_costs[(round_id, reviewer.name)] = review_cost

                    # Verify output count
                    if len(outputs) != len(eligible_indices):
                        raise ReviewWorkflowError(
                            f"Reviewer {reviewer.name} returned {len(outputs)} outputs "
                            f"for {len(eligible_indices)} inputs"
                        )

                    # Process outputs with content validation
                    processed_outputs = []

                    for output, expected_hash in zip(outputs, text_input_hashes):
                        try:
                            if isinstance(output, dict):
                                processed_output = output
                            else:
                                processed_output = json.loads(output)

                            # Add content hash to output for validation
                            processed_output["_text_hash"] = expected_hash
                            processed_outputs.append(processed_output)

                        except Exception as e:
                            self._log(f"Warning: Error processing output: {e}")
                            processed_outputs.append({"reasoning": None, "score": None, "_text_hash": expected_hash})

                    # Update dataframe with validated outputs
                    output_dict = dict(zip(eligible_indices, processed_outputs))
                    df.loc[eligible_indices, output_col] = pd.Series(output_dict)
                    
                    for response_keyword in response_keywords:
                        response_col = f"round-{round_id}_{reviewer.name}_{response_keyword}"
                        response_dict = dict(zip(eligible_indices, [processed_output[response_keyword] for processed_output in processed_outputs]))
                        df.loc[eligible_indices, response_col] = pd.Series(response_dict)

                    self._log(f"The following columns are present in the dataframe at the end of {reviewer.name}'s reivew in round {round_id}: {df.columns.tolist()}")
            return df

        except Exception as e:
            raise ReviewWorkflowError(f"Error running workflow: {e}")

    def _log(self, x):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(x)

    def get_total_cost(self) -> float:
        """Return the total cost of the review process."""
        return sum(self.reviewer_costs.values())
