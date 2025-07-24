import requests
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)


def get_smiles_by_name(compound_name: str) -> str | dict[str, str]:
    """
    Fetches the Canonical SMILES string for a given compound name using the PubChem PUG REST API.

    Args:
        compound_name (str): The name of the compound to search for.

    Returns:
        str: The Canonical SMILES string if found.
        dict[str, str]: A dictionary containing an "error" key with the error message if not found or an error occurs.
    """

    encoded_name = quote(compound_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/CanonicalSMILES/TXT"

    try:
        logger.info(f"Fetching SMILES for compound: {compound_name}")
        r = requests.get(url)

        if not r.ok:
            raise RuntimeError(
                f"Failed to fetch SMILES for '{compound_name}', HTTP status code: {r.status_code}"
            )

        smiles = r.text.rstrip()

        if "NotFound" in smiles:
            error_msg = f"Compound '{compound_name}' not found in PubChem."
            logger.warning(error_msg)
            return {"error": error_msg}

        logger.info(f"Successfully fetched SMILES for {compound_name}")
        return smiles

    except requests.exceptions.RequestException as e:
        error_msg = (
            f"Network error occurred while fetching SMILES for '{compound_name}': {e}"
        )
        logger.error(error_msg)
        return {"error": error_msg}
    except RuntimeError as e:
        logger.warning(e)
        return {"error": str(e)}
    except Exception as e:
        error_msg = f"An unexpected error occurred while fetching SMILES for '{compound_name}': {e}"
        logger.error(error_msg)
        return {"error": error_msg}
