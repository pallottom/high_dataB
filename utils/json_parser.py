# json_parser.py
"""
Functions to parse substance JSON data and prepare records for database insertion.
"""
import json
import re
from typing import List, Dict, Any
import Levenshtein
import os


def parse_possible_multiple_json_objects(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data.get("common_name", data)
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass
    obj_texts = re.findall(r'\{(?:[^{}]|(?R))*\}', text, flags=re.DOTALL)
    objs = []
    for ot in obj_texts:
        try:
            objs.append(json.loads(ot))
        except json.JSONDecodeError:
            try:
                objs.append(json.loads(ot.strip()))
            except json.JSONDecodeError:
                continue
    return objs


def normalize_name(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip().lower()


def match_name_against_synonyms(name: str, synonyms: List[str]) -> bool:
    if not synonyms:
        return False
    target = normalize_name(name)
    for syn in synonyms:
        if normalize_name(syn) == target:
            return True
    return False


def prepare_record_from_obj(obj: Dict[str, Any]) -> Dict[str, Any]:
    common_name = obj.get('common_name') or obj.get('IUPACname')
    synonyms = obj.get('depositor_supplied_synonyms') or []
    if isinstance(synonyms, str):
        synonyms = [s.strip() for s in synonyms.split(',') if s.strip()]
    elif not isinstance(synonyms, list):
        synonyms = list(synonyms) if synonyms else []
    return {
        'common_name': common_name,
        'synonyms': synonyms,
        'inchi': obj.get('InChI'),
        'smiles': obj.get('SMILES'),
        'raw_json': obj,
    }


def find_in_json_directory(word: str, json_path: str, use_levenshtein: bool = True, threshold: int = 1) -> List[Dict[str, Any]]:
    """Search for a word in synonyms of JSON file, return all matching entries."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def matches(target: str, synonyms: List[str]) -> bool:
        """Check if target matches any synonym using exact or fuzzy matching."""
        norm_target = normalize_name(target)
        for syn in synonyms:
            norm_syn = normalize_name(syn)
            
            if use_levenshtein:
                # Use Levenshtein distance with threshold
                distance = Levenshtein.distance(norm_target, norm_syn)
                if distance <= threshold:
                    return True
            else:
                # Exact match
                if norm_target == norm_syn:
                    return True
        return False

    entries = data if isinstance(data, list) else [data]
    matches_found = []
    
    for entry in entries:
        synonyms = entry.get("depositor_supplied_synonyms", [])
        if matches(word, synonyms):
            # Return the common_name if available, otherwise the full entry
            result = entry.get("common_name", entry)
            matches_found.append(result)

    return matches_found


# Test - returns all entries where "ethanol" appears in synonyms
#match1 = find_in_json_directory("alcol etilico", "Ontology1.json")
#match2 = find_in_json_directory("ethanol", "Ontology1.json")

#print(f"Match 1 (alcool etilico): {match1}")
#print(f"Match 2 (ethanol): {match2}")

# Example showing multiple matches
#print("\nAll entries containing 'ethanol' in synonyms:")
#all_ethanol_matches = find_in_json_directory("ethanol", "Ontology1.json")
#for i, match in enumerate(all_ethanol_matches, 1):
#    print(f"  {i}. {match}")