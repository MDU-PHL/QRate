from .operators import evaluate_condition
import yaml
import os

def has_field_action(rule, field):
    """Check if a rule has an action for the specified field."""
    for action in rule.get('actions', []):
        if action.get('field') == field:
            return True
    return False

def check_rule_conditions(row, rule):
    for condition in rule.get('conditions', []):
        if not evaluate_condition(row, condition):
            return False
    return True

def get_rule_action(rule, field):
    for action in rule.get('actions', []):
        if action.get('field') == field:
            return action.get('value')
    return None

def get_rule_comment(rule):
    """Extract COMMENT value from rule actions."""
    for action in rule.get('actions', []):
        if action.get('field') == 'COMMENT':
            return action.get('value', '')
    return ''

def evaluate_mms_rule(row, rules, field, verbose=False):
    """Evaluate all matching rules for a field and aggregate results."""
    relevant_rules = [rule for rule in rules if has_field_action(rule, field)]
    matched_rules = []
    rule_evaluations = []
    skipped_rules = set()
    
    # First pass: identify which rules are met and which should be skipped
    for rule in relevant_rules:
        rule_met = check_rule_conditions(row, rule)
        rule_evaluations.append({
            'rule_id': rule.get('id', 'unknown'),
            'description': rule.get('description', ''),
            'conditions_met': rule_met
        })
        
        if rule_met:
            
            # If this rule is met, add any rules it wants to skip to the skip set
            skip_list = rule.get('skip_rules', [])
            skipped_rules.update(skip_list)
            
            action = get_rule_action(rule, field)
            comment = get_rule_comment(rule)
            if action:  # Only add if there's an action for this field
                matched_rules.append({
                    'status': action,
                    'comment': comment,
                    'rule_id': rule.get('id', 'unknown')
                })
    
    # if matched_rules:
    #     # Aggregate multiple matching rules
    #     result = aggregate_rule_results(matched_rules)
    #     result['rule_evaluations'] = rule_evaluations
    #     return result
    
    # Second pass: filter out skipped rules
    filtered_matched_rules = []
    for rule_result in matched_rules:
        if rule_result['rule_id'] not in skipped_rules:
            filtered_matched_rules.append(rule_result)
        elif verbose:
            print(f"    → Rule {rule_result['rule_id']} skipped due to skip_rules directive")
    
    # Update rule evaluations to show skipped status
    for eval_info in rule_evaluations:
        if eval_info['rule_id'] in skipped_rules and eval_info['conditions_met']:
            eval_info['skipped'] = True
    
    if filtered_matched_rules:
        # Aggregate remaining matching rules
        result = aggregate_rule_results(filtered_matched_rules)
        result['rule_evaluations'] = rule_evaluations
        return result
    
    # No rules matched - return None to indicate no change should be made
    return {'status': None, 'comment': '', 'rule_id': 'no_match', 'rule_evaluations': rule_evaluations}


def aggregate_rule_results(matched_rules):
    """Aggregate multiple rule results, prioritizing FAIL > FLAG > PASS.
    If FAIL is present, only aggregate FAIL comments. Otherwise, aggregate FLAG and PASS comments in priority order.
    """
    # Sort by priority: FAIL > FLAG > PASS
    priority_order = {'FAIL': 0, 'FLAG': 1, 'PASS': 2}
    sorted_rules = sorted(matched_rules, key=lambda x: priority_order.get(x['status'], 3))
    final_status = sorted_rules[0]['status']

    if final_status == 'FAIL':
        # Only aggregate FAIL comments and rule_ids
        comments = [rule['comment'] for rule in matched_rules if rule['status'] == 'FAIL' and rule['comment']]
        rule_ids = [rule['rule_id'] for rule in matched_rules if rule['status'] == 'FAIL']
    else:
        # Aggregate FLAG and PASS comments in priority order
        comments = [rule['comment'] for rule in sorted_rules if rule['status'] in ['FLAG', 'PASS'] and rule['comment']]
        rule_ids = [rule['rule_id'] for rule in sorted_rules if rule['status'] in ['FLAG', 'PASS']]

    combined_comment = '; '.join(comments)

    return {
        'status': final_status,
        'comment': combined_comment,
        'rule_id': ','.join(rule_ids)
    }

def determine_final_result(mms103_result, mms109_result, original_row):
    """
    Determine final result based on MMS103 and MMS109 results.
    Uses comments from rules.yaml instead of generating new ones.
    Preserves original values when no rules are matched.
    
    Logic:
    - MMS103 rules only affect MMS103
    - MMS109 rules only affect MMS109
    - FAIL propagation: If either MMS103 or MMS109 is FAIL (due to matched rules), both become FAIL
    - TEST_QC = FAIL if either MMS103 or MMS109 is FAIL, otherwise PASS
    - Original values are preserved when no rules are matched
    """
    mms103_status = mms103_result['status']
    mms109_status = mms109_result['status']
    
    # Get original values to preserve when no rules match
    original_mms103 = original_row.get('MMS103', 'PASS')
    original_mms109 = original_row.get('MMS109', 'PASS')
    original_comment = original_row.get('COMMENT', '')
    
    # Determine final MMS103 value (only if rules were matched)
    final_mms103 = mms103_status if mms103_status is not None else original_mms103
    
    # Determine final MMS109 value (only if rules were matched)
    final_mms109 = mms109_status if mms109_status is not None else original_mms109
    
    # FAIL propagation logic: Only apply if at least one rule was matched and resulted in FAIL
    # Check if any rule was actually matched (not just preserved original values)
    mms103_rule_matched = mms103_status is not None
    mms109_rule_matched = mms109_status is not None
    
    # Apply FAIL propagation only if rules were matched and resulted in FAIL
    if (mms103_rule_matched and final_mms103 == 'FAIL') or (mms109_rule_matched and final_mms109 == 'FAIL'):
        final_mms103 = 'FAIL'
        final_mms109 = 'FAIL'
    
    # Determine TEST_QC based on final MMS103 and MMS109 values
    # TEST_QC = FAIL if either MMS103 or MMS109 is FAIL, otherwise PASS
    final_test_qc = 'FAIL' if final_mms103 == 'FAIL' or final_mms109 == 'FAIL' else 'PASS'
    
    # Determine final comment - combine comments from matched rules
    comments = []
    if mms103_result['comment'] and mms103_status is not None:
        comments.append(mms103_result['comment'])
    if mms109_result['comment'] and mms109_status is not None:
        comments.append(mms109_result['comment'])
    
    # Use combined comments if available, otherwise preserve original
    final_comment = '; '.join(comments) if comments else original_comment
    
    return {
        'mms103': final_mms103,
        'mms109': final_mms109,
        'test_qc': final_test_qc,
        'comment': final_comment
    }

class CurationEngine:
    def __init__(self, rules, verbose=False):
        self.rules = rules
        self.verbose = verbose

    def curate_data(self, qc_data):
        processed_data = []
        for row in qc_data:
            if self.verbose:
                curated_row, rule_details = self.curate_single_entry(row)
                processed_data.append(curated_row)
                self.log_curation_changes(row, curated_row, rule_details)
            else:
                curated_row = self.curate_single_entry(row)
                processed_data.append(curated_row)
        return processed_data

    def curate_single_entry(self, row):
        mms103_result = evaluate_mms_rule(row, self.rules, 'MMS103', verbose=self.verbose)
        mms109_result = evaluate_mms_rule(row, self.rules, 'MMS109', verbose=self.verbose)
        final_result = determine_final_result(mms103_result, mms109_result, row)
        
        # Store rule evaluations for verbose logging
        if self.verbose:
            final_result['mms103_evaluations'] = mms103_result.get('rule_evaluations', [])
            final_result['mms109_evaluations'] = mms109_result.get('rule_evaluations', [])
        
        # Apply results to row
        result_row = row.copy()
        result_row['MMS103'] = final_result['mms103']
        result_row['MMS109'] = final_result['mms109']
        result_row['TEST_QC'] = final_result['test_qc']
        result_row['COMMENT'] = final_result['comment']
        
        if self.verbose:
            return result_row, final_result
        else:
            return result_row

    def log_curation_changes(self, original_row, curated_row, rule_details=None):
        """Log changes made during curation if verbose mode is enabled."""
        isolate = original_row.get('ISOLATE', 'unknown')
        
        print(f"\n=== Processing Sample: {isolate} ===")
        
        # Log rule evaluations if available
        if rule_details:
            print("Rule Evaluations:")
            
            # MMS103 rules
            if rule_details.get('mms103_evaluations'):
                print("  MMS103 Rules:")
                matched_any_mms103 = False
                for eval_info in rule_details['mms103_evaluations']:
                    if eval_info.get('skipped'):
                        status = "⚠️ SKIPPED (conditions met but rule skipped)"
                    elif eval_info['conditions_met']:
                        status = "✓ MET"
                        matched_any_mms103 = True
                    else:
                        status = "✗ NOT MET"
                    print(f"    - {eval_info['rule_id']}: {status}")
                    print(f"      Description: {eval_info['description']}")
                    # status = "✓ MET" if eval_info['conditions_met'] else "✗ NOT MET"
                    # print(f"    - {eval_info['rule_id']}: {status}")
                    # print(f"      Description: {eval_info['description']}")
                    # if eval_info['conditions_met']:
                    #     matched_any_mms103 = True
                
                if not matched_any_mms103:
                    print("    → No MMS103 rules matched - original value preserved")
            
            # MMS109 rules
            if rule_details.get('mms109_evaluations'):
                print("  MMS109 Rules:")
                matched_any_mms109 = False
                for eval_info in rule_details['mms109_evaluations']:
                    if eval_info.get('skipped'):
                        status = "⚠️ SKIPPED (conditions met but rule skipped)"
                    elif eval_info['conditions_met']:
                        status = "✓ MET"
                        matched_any_mms109 = True
                    else:
                        status = "✗ NOT MET"
                    print(f"    - {eval_info['rule_id']}: {status}")
                    print(f"      Description: {eval_info['description']}")
                    # status = "✓ MET" if eval_info['conditions_met'] else "✗ NOT MET"
                    # print(f"    - {eval_info['rule_id']}: {status}")
                    # print(f"      Description: {eval_info['description']}")
                    # if eval_info['conditions_met']:
                    #     matched_any_mms109 = True
                
                if not matched_any_mms109:
                    print("    → No MMS109 rules matched - original value preserved")
        
        # Log field changes (compare original to final)
        changes = []
        for field in ['MMS103', 'MMS109', 'TEST_QC', 'COMMENT']:
            if original_row.get(field) != curated_row.get(field):
                changes.append(f"{field}: {original_row.get(field)} -> {curated_row.get(field)}")
        
        if changes:
            print("Final Field Changes:")
            for change in changes:
                print(f"  - {change}")
        else:
            print("No field changes made")
        
        print("-" * 50)
