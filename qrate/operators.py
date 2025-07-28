import yaml
import os
import pkg_resources

def evaluate_condition(row, condition):
    """Evaluate a single condition against a row of QC data.
    
    Args:
        row: Dictionary representing a QC result row
        condition: Dictionary with field, operator, and value(s)
        
    Returns:
        Boolean indicating whether the condition is met
    """
    field = condition.get('field')
    operator = condition.get('operator')
    value = condition.get('value')
    
    # Handle missing fields gracefully
    if field not in row:
        return False
    
    # Get field value, handling type conversion
    field_value = row[field]
    
    # Convert string representations of booleans
    if isinstance(value, bool):
        if field_value.lower() == 'true':
            field_value = True
        elif field_value.lower() == 'false':
            field_value = False
    
    # Convert to numbers for numeric comparisons
    if operator in ['<', '<=', '>', '>=']:
        try:
            field_value = float(field_value) if field_value else 0
            value = float(value)
        except ValueError:
            return False
    
    # Evaluate based on operator
    if operator == "==":
        return field_value == value
    elif operator == "!=":
        return field_value != value
    elif operator == "<":
        return field_value < value
    elif operator == "<=":
        return field_value <= value
    elif operator == ">":
        return field_value > value
    elif operator == ">=":
        return field_value >= value
    elif operator == "contains":
        # Case-insensitive string matching
        return str(value).lower() in str(field_value).lower()
        
    elif operator == "outside_pct":
        # Special operator for checking if values are OUTSIDE percentage-based range 
        min_field = condition.get('min_field')
        max_field = condition.get('max_field')
        pct = float(condition.get('pct', 0.1))  # Default to 10%
        
        # Handle missing bounds fields
        if min_field not in row or max_field not in row:
            return False
            
        try:
            # Extract values and convert to float
            min_value = float(row[min_field]) if row[min_field] and row[min_field] != '-' else None
            max_value = float(row[max_field]) if row[max_field] and row[max_field] != '-' else None
            field_value = float(field_value) if field_value else 0
            
            # Can't calculate range if either bound is missing
            if min_value is None or max_value is None:
                return False
                
            # Calculate extended range with percentage
            extended_min = min_value * (1 - pct)
            extended_max = max_value * (1 + pct)
            
            # Check if value is OUTSIDE extended range
            is_outside = field_value < extended_min or field_value > extended_max
            
            # Return result based on expected value
            # If value is True, return True when field is outside range
            # If value is False, return True when field is NOT outside range (i.e., inside range)
            if value is True:
                return is_outside
            elif value is False:
                return not is_outside
            else:
                # Default behavior (backward compatibility) - return True when outside
                return is_outside
            
        except (ValueError, TypeError):
            return False
        
    elif operator == "species_scheme_compatible":
        # Special operator to check if SPECIES_OBS is compatible with SCHEME
        # This requires loading the species scheme mapping
        
        try:
            # Try to find config file relative to package
            try:
                config_path = pkg_resources.resource_filename('qrate', 'config/species_scheme_mapping.yaml')
            except:
                config_path = os.path.join(os.path.dirname(__file__), 'config', 'species_scheme_mapping.yaml')
                
            with open(config_path, 'r') as f:
                mapping = yaml.safe_load(f)
        except:
            return False
        
        species_obs = row.get('SPECIES_OBS', '')
        scheme = row.get('SCHEME', '')
        
        # print(f"DEBUG SCHEME_COMPATIBLE: SPECIES_OBS='{species_obs}', SCHEME='{scheme}'")
        # print(f"DEBUG: Available schemes: {list(mapping.keys()) if mapping else 'None'}")
    
        if not mapping or scheme not in mapping:
            # print(f"DEBUG: Scheme '{scheme}' not found in mapping, returning False")
            return False
        
        compatible_species = mapping[scheme]
        is_compatible = species_obs in compatible_species
        # print(f"DEBUG: Compatible species for '{scheme}': {compatible_species}")
        # print(f"DEBUG: Is '{species_obs}' in compatible list? {is_compatible}")
        
        # Return result based on expected value
        # If value is True, return True when species IS compatible
        # If value is False, return True when species is NOT compatible
        if value is True:
            return is_compatible
        elif value is False:
            return not is_compatible
        else:
            # Default behavior (backward compatibility) - return True when compatible
            return is_compatible
    
    elif operator == "genus_level_match":
        # Special operator to check if SPECIES_OBS matches at genus level with SPECIES_EXP
        # when SPECIES_EXP is in "<genus> species" format
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Extract genus from SPECIES_EXP (first word)
        genus_exp = species_exp.split()[0] if species_exp else ''
        
        # Extract genus from SPECIES_OBS (first word)
        genus_obs = species_obs.split()[0] if species_obs else ''
        
        # Check if genus matches (case-insensitive)
        genus_matches = genus_exp.lower() == genus_obs.lower() if genus_exp and genus_obs else False
        
        # Return result based on expected value
        # If value is True, return True when genus DOES match
        # If value is False, return True when genus does NOT match
        if value is True:
            return genus_matches
        elif value is False:
            return not genus_matches
        else:
            # Default behavior (backward compatibility) - return True when matches
            return genus_matches
    
    elif operator == "species_subspecies_match":
        # SPECIES_EXP contains "ssp" and SPECIES_OBS matches the base species part
        # e.g., "Salmonella enterica ssp enterica" vs "Salmonella enterica"
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Check if SPECIES_EXP contains "ssp"
        if " ssp " not in species_exp.lower():
            subspecies_match = False
        else:
            # Extract the base species part (everything before " ssp ")
            base_species = species_exp.split(" ssp ")[0].strip()
            
            # Check if SPECIES_OBS matches the base species (case-insensitive)
            subspecies_match = species_obs.lower() == base_species.lower()
        
        # Return result based on expected value
        # If value is True, return True when subspecies DOES match
        # If value is False, return True when subspecies does NOT match
        if value is True:
            return subspecies_match
        elif value is False:
            return not subspecies_match
        else:
            # Default behavior (backward compatibility) - return True when matches
            return subspecies_match
    
    elif operator == "species_different_genus_match":
        # Both species are specific (not generic), have same genus, but are different species
        # Excludes cases where either contains "species" or "ssp"
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Both should not contain "species" or "ssp"
        if (" species" in species_obs.lower() or " species" in species_exp.lower() or
            " ssp " in species_obs.lower() or " ssp " in species_exp.lower()):
            different_genus_match = False
        else:
            # Extract genus from both
            genus_obs = species_obs.split()[0] if species_obs else ''
            genus_exp = species_exp.split()[0] if species_exp else ''
            
            # Check if genus matches but species are different
            different_genus_match = (genus_obs and genus_exp and 
                    genus_obs.lower() == genus_exp.lower() and 
                    species_obs.lower() != species_exp.lower())
        
        # Return result based on expected value
        # If value is True, return True when there IS a different genus match
        # If value is False, return True when there is NOT a different genus match
        if value is True:
            return different_genus_match
        elif value is False:
            return not different_genus_match
        else:
            # Default behavior (backward compatibility) - return True when matches
            return different_genus_match
    
    elif operator == "species_genus_mismatch":
        # SPECIES_EXP and SPECIES_OBS have different genera (complete mismatch)
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Extract genus from both
        genus_obs = species_obs.split()[0] if species_obs else ''
        genus_exp = species_exp.split()[0] if species_exp else ''
        
        # Check if genera are different (case-insensitive)
        genus_mismatch = (genus_obs and genus_exp and 
                genus_obs.lower() != genus_exp.lower())
        
        # Return result based on expected value
        # If value is True, return True when genera DO mismatch
        # If value is False, return True when genera do NOT mismatch
        if value is True:
            return genus_mismatch
        elif value is False:
            return not genus_mismatch
        else:
            # Default behavior (backward compatibility) - return True when mismatch
            return genus_mismatch
    
    elif operator == "species_synonym_match":
        # Special operator to check if SPECIES_OBS is a synonym of SPECIES_EXP
        # This requires loading the species synonym mapping
        
        try:
            # Try to find config file relative to package
            try:
                config_path = pkg_resources.resource_filename('qrate', 'config/species_synonym_mapping.yaml')
            except:
                config_path = os.path.join(os.path.dirname(__file__), 'config', 'species_synonym_mapping.yaml')
                
            with open(config_path, 'r') as f:
                mapping = yaml.safe_load(f)
        except:
            synonym_match = False
        else:
            species_obs = row.get('SPECIES_OBS', '').strip()
            species_exp = row.get('SPECIES_EXP', '').strip()
            
            if not mapping or 'synonyms' not in mapping:
                synonym_match = False
            else:
                synonyms = mapping['synonyms']
                
                # Check if SPECIES_OBS is a synonym for SPECIES_EXP
                synonym_match = synonyms.get(species_obs) == species_exp
        
        # Return result based on expected value
        # If value is True, return True when species IS a synonym
        # If value is False, return True when species is NOT a synonym
        if value is True:
            return synonym_match
        elif value is False:
            return not synonym_match
        else:
            # Default behavior (backward compatibility) - return True when synonym
            return synonym_match
                        
    # Unrecognized operator
    return False
