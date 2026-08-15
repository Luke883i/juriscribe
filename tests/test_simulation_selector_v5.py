import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "simulate_v5_ci.py"
spec = importlib.util.spec_from_file_location("juriscribe_simulate_v5_ci", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class SimulationSelectorV5Tests(unittest.TestCase):
    def test_sha256_rng_known_vectors(self):
        vectors = [
            (11, 10, [1, 7]),
            (99991, 8, [6, 2]),
            (47, 4, [2, 2]),
        ]
        for seed, stop, expected in vectors:
            rng = module.StableRandom(seed)
            self.assertEqual([rng.randrange(stop), rng.randrange(stop)], expected)

    def test_rng_is_stateless_across_instances(self):
        left = module.StableRandom(509)
        right = module.StableRandom(509)
        self.assertEqual([left.randrange(17) for _ in range(8)], [right.randrange(17) for _ in range(8)])
        self.assertEqual(module.SELECTOR_VERSION, "sha256-stable-roundrobin-v2")


if __name__ == "__main__":
    unittest.main()
