import logging
from pathlib import Path
from config_logging import setup_logging

from run_binding_markup import run_markup


CHECKPOINTS_FOLDER = Path("/home/alex/dev/test-repkAI/data/checkpoint_that_one_sample")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Marking regions of interest...")
    run_markup(CHECKPOINTS_FOLDER)

    logger.info("Finished parsing!")


if __name__ == "__main__":
    main()
