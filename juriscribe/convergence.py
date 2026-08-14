from dataclasses import dataclass

@dataclass
class ConvergenceMonitor:
    semantic_no_novelty_streak: int = 0
    strategy_no_improvement_streak: int = 0
    semantic_target: int = 1000
    strategy_target: int = 1000

    def semantic_probe(self, novelty: bool, new_contradiction: bool = False) -> bool:
        self.semantic_no_novelty_streak = 0 if novelty or new_contradiction else self.semantic_no_novelty_streak + 1
        return self.semantic_saturated

    def strategy_probe(self, material_improvement: bool) -> bool:
        self.strategy_no_improvement_streak = 0 if material_improvement else self.strategy_no_improvement_streak + 1
        return self.strategy_saturated

    @property
    def semantic_saturated(self) -> bool:
        return self.semantic_no_novelty_streak >= self.semantic_target

    @property
    def strategy_saturated(self) -> bool:
        return self.strategy_no_improvement_streak >= self.strategy_target
