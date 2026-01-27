# Wrapper to import rulebase functions without executing main code
import ast
import types

def _load_rulebase_functions():
    with open("rulebase.py", "r", encoding="utf-8") as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Filter only function and class definitions, imports
    new_body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign)):
            # Skip assignments that call functions (like user = get_user_input_from_inbody())
            if isinstance(node, ast.Assign):
                # Check if it is a simple constant assignment
                if isinstance(node.value, ast.Call):
                    continue
            new_body.append(node)
    
    tree.body = new_body
    
    code = compile(tree, "rulebase.py", "exec")
    namespace = {}
    exec(code, namespace)
    return namespace

_funcs = _load_rulebase_functions()

# Export main functions
classify_bmi = _funcs["classify_bmi"]
classify_body_fat_rate = _funcs["classify_body_fat_rate"]
classify_muscle_level = _funcs["classify_muscle_level"]
stage1_body_type = _funcs["stage1_body_type"]
stage2_adjust = _funcs["stage2_adjust"]
analyze_stage1_2 = _funcs["analyze_stage1_2"]
classify_part_level = _funcs["classify_part_level"]
classify_body_parts = _funcs["classify_body_parts"]
classify_body_fat_parts = _funcs["classify_body_fat_parts"]
is_numeric_seg = _funcs["is_numeric_seg"]
normalize_muscle_seg = _funcs["normalize_muscle_seg"]
normalize_fat_seg = _funcs["normalize_fat_seg"]
get_distribution = _funcs["get_distribution"]
stage3_classification = _funcs["stage3_classification"]
full_body_analysis_from_inbody = _funcs["full_body_analysis_from_inbody"]
