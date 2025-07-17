from operators import evaluate_condition

def evaluate_mms_rule(row, rules, field):
    relevant_rules = [rule for rule in rules if field in str(rule)]
    for rule in relevant_rules:
        if check_rule_conditions(row, rule):
            action = get_rule_action(rule, field)
            comment = generate_comment(rule, field, action)
            return {'status': action, 'comment': comment, 'rule_id': rule.get('id', 'unknown')}
    return {'status': 'PASS', 'comment': '', 'rule_id': 'default'}

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

def generate_comment(rule, field, action):
    base_comment = rule.get('description', '')
    if action == 'FAIL':
        return f"{field} FAIL due to {base_comment}"
    elif action == 'FLAG':
        return f"{field} FLAG as {base_comment}"
    elif action == 'PASS':
        return f"{field} Manual PASS as {base_comment}"
    return base_comment

def determine_final_result(mms103_result, mms109_result):
    """
    Determine final result based on MMS103 and MMS109 results.
        
    Logic:
    1. If either is FAIL, final result is FAIL with single comment
    2. If both are PASS, final result is PASS
    3. If Manual PASS and FLAG, append both comments
    """
    mms103_status = mms103_result['status']
    mms109_status = mms109_result['status']
        
    # If FAIL, just a single comment irrespective of MMS103 or MMS109
    if mms103_status == 'FAIL' or mms109_status == 'FAIL':
        fail_comment = mms103_result['comment'] if mms103_status == 'FAIL' else mms109_result['comment']
        return {
            'mms103': 'FAIL',
            'mms109': 'FAIL',
            'test_qc': 'FAIL',
            'comment': fail_comment
            }
        
    # If Manual PASS and FLAG, append both comments
    if ((mms103_status == 'PASS' and mms109_status == 'FLAG') or 
            (mms103_status == 'FLAG' and mms109_status == 'PASS')):
            
            comments = []
            if mms103_result['comment']:
                comments.append(f"MMS103: {mms103_result['comment']}")
            if mms109_result['comment']:
                comments.append(f"MMS109: {mms109_result['comment']}")
            
            combined_comment = "; ".join(comments)
            
            return {
                'mms103': mms103_status,
                'mms109': mms109_status,
                'test_qc': 'PASS',  # Overall PASS if no failures
                'comment': combined_comment
            }
        
    # Both FLAG
    if mms103_status == 'FLAG' and mms109_status == 'FLAG':
            comments = []
            if mms103_result['comment']:
                comments.append(f"MMS103: {mms103_result['comment']}")
            if mms109_result['comment']:
                comments.append(f"MMS109: {mms109_result['comment']}")
            
            combined_comment = "; ".join(comments)
            
            return {
                'mms103': 'FLAG',
                'mms109': 'FLAG',
                'test_qc': 'FLAG',
                'comment': combined_comment
            }
        
    # Both PASS
    if mms103_status == 'PASS' and mms109_status == 'PASS':
            # Use the comment from whichever rule was applied, or combine if both have comments
            comments = []
            if mms103_result['comment']:
                comments.append(mms103_result['comment'])
            if mms109_result['comment'] and mms109_result['comment'] != mms103_result['comment']:
                comments.append(mms109_result['comment'])
            
            combined_comment = "; ".join(comments) if comments else ""
            
            return {
                'mms103': 'PASS',
                'mms109': 'PASS',
                'test_qc': 'PASS',
                'comment': combined_comment
            }
        
    # Default case
    return {
            'mms103': mms103_status,
            'mms109': mms109_status,
            'test_qc': 'PASS',
            'comment': ""
        }

class CurationEngine:
    def __init__(self, rules, verbose=False):
        self.rules = rules
        self.verbose = verbose

    def curate_data(self, qc_data):
        processed_data = []
        for row in qc_data:
            original_row = row.copy()
            curated_row = self.curate_single_entry(row)
            processed_data.append(curated_row)
            if self.verbose:
                self.log_curation_changes(original_row, curated_row)
        return processed_data

    def curate_single_entry(self, row):
        mms103_result = evaluate_mms_rule(row, self.rules, 'MMS103')
        mms109_result = evaluate_mms_rule(row, self.rules, 'MMS109')
        final_result = determine_final_result(mms103_result, mms109_result)
        row['MMS103'] = final_result['mms103']
        row['MMS109'] = final_result['mms109']
        row['TEST_QC'] = final_result['test_qc']
        row['COMMENT'] = final_result['comment']
        return row

    def log_curation_changes(self, original_row, curated_row):
        """Log changes made during curation if verbose mode is enabled."""
        isolate = original_row.get('ISOLATE', 'unknown')
        
        changes = []
        for field in ['MMS103', 'MMS109', 'TEST_QC', 'COMMENT']:
            if original_row.get(field) != curated_row.get(field):
                changes.append(f"{field}: {original_row.get(field)} -> {curated_row.get(field)}")
        
        if changes:
            print(f"Sample {isolate}: {'; '.join(changes)}")
