from typing import List, Tuple

from datasets import Dataset


class RewardModel(object):
    def __init__(
        self,
    ):
        pass

    def train(self, dataset: Dataset) -> "RewardModel":
        """
        Train the reward model on the given dataset.

        Args:
            dataset (Dataset): The dataset to train on. A single example is a dictionary with the following keys:
                - "intent": str The intent of the statement.
                - "targetGroup": str The target group of the statement.
                - "relevantPowerDynamics": str The relevant power dynamics of the statement.
                - "implication": str The implication of the statement.
                - "targetGroupEmotionalReaction": str The emotional reaction of the target group to the statement.
                - "targetGroupCognitiveReaction": str The cognitive reaction of the target group to the statement.
                - "offensiveness": str The offensiveness of the statement.
                - "labels": Tuple[int, int, int, int, int, int, int] The labels for the example.

        Returns:
            RewardModel: The trained reward model.
        """
        raise NotImplementedError

    def predict(
        self, dataset: Dataset
    ) -> List[Tuple[int, int, int, int, int, int, int]]:
        raise NotImplementedError