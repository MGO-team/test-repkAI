import dataclasses
import json
import logging
import os
import random
import time

from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from typing import Any

from parse_pdfs import parse_pdfs_in_dir
from config import CHECKPOINTS_FOLDER

logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("MODEL")


def ask_llm(
    content,
    system_prompt,
    data_model: Any | None = None,
    base_url: str = BASE_URL,
    api_key: str = API_KEY,
    model: str = MODEL,
    n_retries_response: int = 3,
    n_retries_response_validation: int = 3,
):
    args = locals()
    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            max_tokens=75,
            temperature=0.5,
        )
    except Exception as e:
        logger.info(e)
        logger.info(f"will retry {args['n_retries_response']} times")
        args["n_retries_response"] = n_retries_response - 1
        time.sleep(random.uniform(2, 3))
        if args["n_retries_response"] >= 0:
            ask_llm(**args)
        else:
            return {"error": e}

    response_message = response.choices[0].message.content

    if not data_model or data_model is None:
        return response_message
    else:
        try:
            cleaned = response_message.strip().replace("json", "", 1).strip()
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            logger.info(e)
            logger.info(f"will retry {args['n_retries_response']} times")
            args["n_retries_response"] = n_retries_response - 1
            time.sleep(random.uniform(2, 3))
            if args["n_retries_response"] >= 0:
                ask_llm(**args)
            else:
                return {"error": e}


system_prompt = "You are an expert in structural biology, chemoinformatics and patents"
content_template = (
    f"Here is a fragment of a patent: {0}. It was autorecognized, so it might have some typos. "
    + "Your task is to define if this fragment has any data on molecule binding with protein. "
    + "Pay special attention to values like: Ki (nM), IC50 (nM), Kd (nM), EC50 (nM)"
    + "You have to return your verdict as a valid json string has_binding_info: true|false. Only json, not other data! Do not use markdown formatting!"
)


def run_markup():  # TODO
    patents = parse_pdfs_in_dir(Path(CHECKPOINTS_FOLDER, "patent_pdfs"))

    results = []
    CHECKPOINTS_FOLDER_BINDING = Path(CHECKPOINTS_FOLDER, "json_binding_data")
    CHECKPOINTS_FOLDER_BINDING.mkdir(exist_ok=True, parents=True)

    for patent in patents:
        for indx, chunk in enumerate(patent.chunks):
            logger.info(
                f"patent={patent.name}, chunk={indx}, pos={chunk.start, chunk.end}"
            )
            content = content_template.format(chunk.text)
            res = ask_llm(content, system_prompt, data_model=True)
            if "error" not in res:
                if "has_binding_info" in res:
                    chunk.has_binding_info = res["has_binding_info"]

                else:
                    logger.info(f"some strange output in {patent.name}: {res.keys()}")

            logger.info(res)
            results.append(res)
        patent_out = patent
        patent_out.local_path = str(patent_out.local_path)
        d = dataclasses.asdict(patent_out)
        filename = Path(CHECKPOINTS_FOLDER_BINDING, f"{patent.name}.json")
        with open(filename, "w") as f:
            json.dump(d, f, indent=4)
