import dataclasses
import json
import logging
import os
import random
import asyncio

from dotenv import load_dotenv
from pathlib import Path
from typing import Any
from openai import AsyncOpenAI
import aiofiles

from parse_pdfs import Patent
from config import CHECKPOINTS_FOLDER, MAX_CONCURRENT_REQUESTS, MIN_PDF_TEXT_LENGTH

logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("MODEL")

api_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
file_semaphore = asyncio.Semaphore(100)


async def ask_llm_async(
    content,
    system_prompt,
    data_model: Any | None = None,
    base_url: str = BASE_URL,
    api_key: str = API_KEY,
    model: str = MODEL,
    n_retries_response: int = 3,
):
    client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async with api_semaphore:  # Limit concurrent API requests
        for attempt in range(n_retries_response + 1):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    max_tokens=75,
                    temperature=0.5,
                )
                break  # Success
            except Exception as e:
                logger.info(f"Attempt {attempt + 1} failed: {e}")
                if attempt < n_retries_response:
                    await asyncio.sleep(random.uniform(2, 3))
                else:
                    return {"error": str(e)}

    response_message = response.choices[0].message.content

    if not data_model:
        return response_message
    else:
        try:
            cleaned = response_message.strip().replace("json", "", 1).strip()
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            logger.info(f"JSON decode error: {e}")
            return {"error": str(e)}


system_prompt = "You are an expert in structural biology, chemoinformatics and patents"
content_template = (
    "Here is a fragment of a patent. It was autorecognized, so it might have some typos. "
    + "Your task is to define if this fragment has any data on molecule binding with protein. "
    + "Pay special attention to values like: Ki (nM), IC50 (nM), Kd (nM), EC50 (nM)"
    + "You have to return your verdict as a valid json string has_binding_info: true|false. Only json, not other data! Do not use markdown formatting!"
)


async def process_chunk(patent, chunk, indx):
    if patent.is_too_short:
        logger.warning(
            f"Skipping processing chunk {indx} for short patent {patent.name}"
        )
        return {"error": "Patent marked as too short"}

    logger.info(f"patent={patent.name}, chunk={indx}, pos={chunk.start, chunk.end}")
    content = content_template + f"Here is a fragment of a patent: {chunk.text}"
    res = await ask_llm_async(content, system_prompt, data_model=True)
    if "error" not in res:
        if "has_binding_info" in res:
            chunk.has_binding_info = res["has_binding_info"]
            if chunk.has_binding_info:
                patent.has_binding_info = True
        else:
            logger.info(f"Some strange output in {patent.name}: {res.keys()}")
    logger.info(res)
    return res


async def save_patent_json(filename, data):
    """Async function to save patent data with file descriptor limiting using aiofiles"""
    async with file_semaphore:
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data, indent=4))


async def run_markup_async(
    patents: list[Patent],
    checkpoints_folder: Path = CHECKPOINTS_FOLDER,
):
    # results = []
    CHECKPOINTS_FOLDER_BINDING = Path(checkpoints_folder, "json_binding_data")
    CHECKPOINTS_FOLDER_BINDING.mkdir(exist_ok=True, parents=True)
    CHECKPOINTS_FOLDER_SUMMARY = Path(checkpoints_folder, "json_binding_summary")
    CHECKPOINTS_FOLDER_SUMMARY.mkdir(exist_ok=True, parents=True)

    # Separate patents based on the is_too_short flag
    normal_patents = [p for p in patents if not p.is_too_short]
    short_patents = [p for p in patents if p.is_too_short]

    logger.info(
        f"Found {len(short_patents)} patents too short (text < {MIN_PDF_TEXT_LENGTH} chars) for processing."
    )
    logger.info(f"Processing {len(normal_patents)} normal patents.")

    save_short_tasks = []
    if short_patents:
        logger.info("Saving data for short patents directly...")
        for patent in short_patents:
            logger.info(f"{patent.name} too short to process")
            patent_out = dataclasses.replace(patent)
            patent_out.local_path = str(patent_out.local_path)
            d = dataclasses.asdict(patent_out)

            filename = Path(CHECKPOINTS_FOLDER_BINDING, f"{patent.name}.json")
            save_task = save_patent_json(filename, d)
            save_short_tasks.append(save_task)

    if save_short_tasks:
        await asyncio.gather(*save_short_tasks)

    tasks = []
    for patent in normal_patents:
        patent_tasks = [
            process_chunk(patent, chunk, indx)
            for indx, chunk in enumerate(patent.chunks)
        ]
        tasks.extend(patent_tasks)

    if tasks:
        await asyncio.gather(*tasks)

    save_normal_tasks = []
    for patent in normal_patents:
        patent_out = dataclasses.replace(patent)
        patent_out.local_path = str(patent_out.local_path)
        d = dataclasses.asdict(patent_out)
        filename = Path(CHECKPOINTS_FOLDER_BINDING, f"{patent.name}.json")
        save_task = save_patent_json(filename, d)
        save_normal_tasks.append(save_task)

    if save_normal_tasks:
        await asyncio.gather(*save_normal_tasks)
