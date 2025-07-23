import logging
import asyncio
from pathlib import Path
from config_logging import setup_logging

from run_binding_markup_async import run_markup_async


CHECKPOINTS_FOLDER = Path("/home/alex/dev/test-repkAI/data/checkpoint_that_one_sample")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Marking regions of interest...")
    
    asyncio.run(run_markup_async(checkpoints_folder=CHECKPOINTS_FOLDER))

    logger.info("Finished parsing!")


if __name__ == "__main__":
    main()