import json
import aiofiles
from typing import Any, List
from langchain.agents import Tool, initialize_agent, AgentType
# from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
import logging
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

from parse_pdfs import Patent
from prot_fasta_parser import get_uniprot_fasta_by_gene
from smiles_parser import get_smiles_by_name

from config import CHECKPOINTS_FOLDER

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("MODEL")

MAX_CONCURRENT_CONNECTIONS = 6
semaphore = asyncio.Semaphore(MAX_CONCURRENT_CONNECTIONS)

# Initialize async LLM
llm = ChatOpenAI(
    model=MODEL,
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,
    temperature=0.0,
    max_tokens=4096, 
)


# Async versions of tools with concurrency control
async def smiles_tool(name: str) -> str:
    async with semaphore:
        # If get_smiles_by_name is sync, run in thread to prevent blocking
        result = await asyncio.to_thread(get_smiles_by_name, name)
        return result or "Not found"


async def uniprot_tool(gene_name: str) -> str:
    async with semaphore:
        # If get_uniprot_fasta_by_gene is sync, run in thread to prevent blocking
        result = await asyncio.to_thread(get_uniprot_fasta_by_gene, gene_name)
        return result or "Not found"


# Define tools using async functions
tools = [
    Tool(
        name="GetSMILES",
        func=smiles_tool,
        description="Use this to convert a ligand name into SMILES notation. Returns 'Not found' if unsuccessful.",
        coroutine=smiles_tool,
    ),
    Tool(
        name="GetFASTA",
        func=uniprot_tool,
        description="Use this to convert a protein name into a FASTA amino acid sequence. Returns 'Not found' if unsuccessful.",
        coroutine=uniprot_tool,
    ),
]

prompt = """
You are an expert cheminformatics and pharmacology data extractor. Your task is to analyze patent text and extract structured binding data.

You are given a part of a text from a patent {text}.

INSTRUCTIONS:
1. Identify ligand mentions (chemical names, references to chemical names (this can be 'example', 'compound', etc.))
2. Determine the ligand name
3. Determine protein name
4. Extract binding constants: Ki, IC50, Kd, EC50 (in nM)
5. Extract assay description
6. Use the GetSMILES tool to convert ligand names to SMILES notation
7. Use the GetFASTA tool to convert protein names to FASTA sequences

RETURN ONLY A VALID JSON OBJECT with these keys:

"Ki_nM": "value or null",
"IC50_nM": "value or null", 
"Kd_nM": "value or null",
"EC50_nM": "value or null",
"assay_description": "brief description of how binding was measured",
"ligand_name": "identified ligand name",
"ligand_SMILES": "SMILES notation from GetSMILES tool or null",
"protein_name": "identified protein name", 
"protein_FASTA": "FASTA sequence from GetFASTA tool or null"

CRITICAL RULES:
- Only extract values that are explicitly stated with units (nM, μM, etc.)
- Convert units appropriately (1 μM = 1000 nM)
- Be conservative - only report high confidence data
- Return ONLY the JSON, no other text
- DO NOT USE MARKDOWN
- DO NOT include "Thought:" or "Action:" in your response
- Use the provided tools when you have identified ligand or protein names
"""

async def process_patent_chunk(chunk_text: str) -> dict[str, Any]:
    try:
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            # verbose=True,
            handle_parsing_errors=True,
        )
        f_prompt = prompt.format(text=chunk_text)
        try:
            result = await asyncio.wait_for(agent.arun(f_prompt), timeout=600)
        except asyncio.TimeoutError:
            logger.warning("Agent timed out processing chunk")
            return {}
        
        # Clean the result
        result = result.strip()
        
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.strip("```json").strip("```")
        
        # Parse JSON
        intermediate_data = json.loads(result)

        final_output = {
            "Ki (nM)": intermediate_data.get("Ki_nM"),
            "IC50 (nM)": intermediate_data.get("IC50_nM"),
            "Kd (nM)": intermediate_data.get("Kd_nM"),
            "EC50 (nM)": intermediate_data.get("EC50_nM"),
            "assay": intermediate_data.get("assay_description", ""),
            "ligand_name": intermediate_data.get("ligand_name"),
            "ligand_SMILES": intermediate_data.get("ligand_SMILES"),
            "protein_name": intermediate_data.get("protein_name"),
            "protein_FASTA": intermediate_data.get("protein_FASTA"),
            "raw_result": result,
        }

        return final_output

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing error processing chunk: {e}")
        logger.warning(f"Raw result was: {result}")
        return {
            "Ki (nM)": None,
            "IC50 (nM)": None,
            "Kd (nM)": None,
            "EC50 (nM)": None,
            "assay": None,
            "ligand_name": None,
            "ligand_SMILES": None,
            "protein_name": None,
            "protein_FASTA": None,
            "raw_result": result,
        }
    except Exception as e:
        logger.warning(f"Error processing chunk: {e}")
        return {}


async def process_all_patents(
    patents: List[Patent], output_dir: str = "patent_results"
) -> List[dict[str, Any]]:
    # Create output directory if it doesn't exist
    output_path = Path(CHECKPOINTS_FOLDER, output_dir)
    output_path.mkdir(exist_ok=True)

    all_results = []

    for patent in patents:
        if not patent.has_binding_info:
            continue

        patent_results = []
        tasks = [
            process_patent_chunk(chunk.text)
            for chunk in patent.chunks
            if chunk.has_binding_info
        ]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in chunk_results:
            if isinstance(res, Exception):
                logger.warning(f"Exception during chunk processing: {res}")
                continue
            if res:
                patent_results.append(res)

        # Save results for this patent immediately as JSON using async files
        if patent_results:
            patent_output_file = output_path / f"{patent.name}.json"
            async with aiofiles.open(patent_output_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(patent_results, indent=2, ensure_ascii=False))

            # Also add to the overall results list
            all_results.extend(patent_results)

            logger.info(f"Saved {len(patent_results)} results for patent {patent.name}")
        else:
            logger.info(f"No binding data found for patent {patent.name}")

    return all_results
