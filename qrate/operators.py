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
        import yaml
        import os
        import pkg_resources
        
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
        
        if not mapping or scheme not in mapping:
            return False
        
        compatible_species = mapping[scheme]
        return species_obs in compatible_species
    
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
        return genus_exp.lower() == genus_obs.lower() if genus_exp and genus_obs else False
    
    elif operator == "species_subspecies_match":
        # SPECIES_EXP contains "ssp" and SPECIES_OBS matches the base species part
        # e.g., "Salmonella enterica ssp enterica" vs "Salmonella enterica"
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Check if SPECIES_EXP contains "ssp"
        if " ssp " not in species_exp.lower():
            return False
        
        # Extract the base species part (everything before " ssp ")
        base_species = species_exp.split(" ssp ")[0].strip()
        
        # Check if SPECIES_OBS matches the base species (case-insensitive)
        return species_obs.lower() == base_species.lower()
    
    elif operator == "species_different_genus_match":
        # Both species are specific (not generic), have same genus, but are different species
        # Excludes cases where either contains "species" or "ssp"
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Both should not contain "species" or "ssp"
        if (" species" in species_obs.lower() or " species" in species_exp.lower() or
            " ssp " in species_obs.lower() or " ssp " in species_exp.lower()):
            return False
        
        # Extract genus from both
        genus_obs = species_obs.split()[0] if species_obs else ''
        genus_exp = species_exp.split()[0] if species_exp else ''
        
        # Check if genus matches but species are different
        return (genus_obs and genus_exp and 
                genus_obs.lower() == genus_exp.lower() and 
                species_obs.lower() != species_exp.lower())
    
    elif operator == "species_genus_mismatch":
        # SPECIES_EXP and SPECIES_OBS have different genera (complete mismatch)
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        # Extract genus from both
        genus_obs = species_obs.split()[0] if species_obs else ''
        genus_exp = species_exp.split()[0] if species_exp else ''
        
        # Check if genera are different (case-insensitive)
        return (genus_obs and genus_exp and 
                genus_obs.lower() != genus_exp.lower())
    
    elif operator == "species_synonym_match":
        # Special operator to check if SPECIES_OBS is a synonym of SPECIES_EXP
        # This requires loading the species synonym mapping
        import yaml
        import os
        import pkg_resources
        
        try:
            # Try to find config file relative to package
            try:
                config_path = pkg_resources.resource_filename('qrate', 'config/species_synonym_mapping.yaml')
            except:
                config_path = os.path.join(os.path.dirname(__file__), 'config', 'species_synonym_mapping.yaml')
                
            with open(config_path, 'r') as f:
                mapping = yaml.safe_load(f)
        except:
            return False
        
        species_obs = row.get('SPECIES_OBS', '').strip()
        species_exp = row.get('SPECIES_EXP', '').strip()
        
        if not mapping or 'synonyms' not in mapping:
            return False
        
        synonyms = mapping['synonyms']
        
        # Check if SPECIES_OBS is a synonym for SPECIES_EXP
        return synonyms.get(species_obs) == species_exp
                        
    # Unrecognized operator
    return False
