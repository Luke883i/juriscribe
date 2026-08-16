"""Current CLI/API pipeline. v0.9 implementation lives in pipeline_v9."""
from .pipeline_v9 import *  # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(main())
