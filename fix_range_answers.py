"""
Script to fix accuracy evaluation for range-based answers in batch test results.
Handles cases where numeric answers fall within an acceptable range but were marked incorrect.
"""

import json
import re
from pathlib import Path


def parse_numeric_value(text):
    """Extract numeric value from text, handling various formats."""
    if text is None:
        return None
    
    text = str(text).strip()
    
    match = re.search(r'-?\d+\.?\d*', text)
    if match:
        return float(match.group())
    return None


def parse_range(range_text):
    """Parse range like '30.0 TO 30.5' or '490 TO 510' into (min, max)."""
    if not range_text or not isinstance(range_text, str):
        return None
    
    range_text = str(range_text).upper().strip()
    
    # Handle "X TO Y" format
    if " TO " in range_text:
        parts = range_text.split(" TO ")
        if len(parts) == 2:
            try:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return (min_val, max_val)
            except ValueError:
                return None
    
    return None


def is_answer_in_range(prediction, correct_answer):
    """
    Check if prediction falls within the correct answer range.
    
    Args:
        prediction: The model's predicted answer
        correct_answer: The correct answer (could be a range like "30.0 TO 30.5")
    
    Returns:
        tuple: (is_correct, reason) where is_correct is bool and reason is explanation string
    """
    # Try to parse as range
    range_tuple = parse_range(correct_answer)
    
    if range_tuple:
        # It's a range-based answer
        min_val, max_val = range_tuple
        pred_val = parse_numeric_value(prediction)
        
        if pred_val is None:
            return (False, f"Could not extract numeric value from prediction: {prediction}")
        
        is_correct = min_val <= pred_val <= max_val
        if is_correct:
            return (True, f"Prediction {pred_val} is within range [{min_val}, {max_val}]")
        else:
            return (False, f"Prediction {pred_val} is outside range [{min_val}, {max_val}]")
    else:
        # Not a range, try exact numeric comparison
        correct_val = parse_numeric_value(correct_answer)
        pred_val = parse_numeric_value(prediction)
        
        if correct_val is not None and pred_val is not None:
            # Allow small tolerance for floating point comparisons
            tolerance = 0.01
            is_correct = abs(correct_val - pred_val) <= tolerance
            if is_correct:
                return (True, f"Prediction {pred_val} matches correct answer {correct_val}")
            else:
                return (False, f"Prediction {pred_val} does not match {correct_val}")
        
        # Fall back to string comparison
        pred_str = str(prediction).strip().upper() if prediction else ""
        correct_str = str(correct_answer).strip().upper() if correct_answer else ""
        
        is_correct = correct_str in pred_str
        if is_correct:
            return (True, f"String match: '{correct_str}' found in '{pred_str}'")
        else:
            return (False, f"No match between '{pred_str}' and '{correct_str}'")


def fix_results_file(input_file, output_file=None):
    """
    Fix accuracy evaluation in results JSON file.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file (if None, overwrites input)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_file}")
        return
    
    # Load results
    print(f"Loading results from: {input_file}")
    with open(input_path, 'r') as f:
        results = json.load(f)
    
    # Track changes
    fixed_count = 0
    total_count = 0
    details = []
    
    # Support both 'questions' (comparison format) and 'results' (batch test format)
    if 'questions' in results:
        # Comparison format with multiple models
        # Dynamically detect model names from the first question
        excluded_keys = {'qid', 'question_text', 'correct_answer', 'topic', 'question_type'}
        sample_question = results['questions'][0] if results['questions'] else {}
        model_names = [key for key in sample_question.keys() if key not in excluded_keys]
        
        for i, question in enumerate(results['questions']):
            qid = question.get('qid', f'Q{i}')
            correct_answer = question.get('correct_answer')
            question_text = question.get('question_text', '')[:80] + '...'
            
            # Check all detected models
            for model_name in model_names:
                if model_name not in question:
                    continue
                
                model_result = question[model_name]
                
                if not model_result.get('success', False):
                    continue
                
                prediction = model_result.get('prediction')
                old_is_correct = model_result.get('is_correct', False)
                
                # Re-evaluate
                new_is_correct, reason = is_answer_in_range(prediction, correct_answer)
                
                # Update if changed
                if old_is_correct != new_is_correct:
                    model_result['is_correct'] = new_is_correct
                    model_result['_fix_reason'] = reason
                    fixed_count += 1
                    
                    details.append({
                        'qid': qid,
                        'model': model_name,
                        'question': question_text,
                        'correct_answer': correct_answer,
                        'prediction': prediction,
                        'old_status': old_is_correct,
                        'new_status': new_is_correct,
                        'reason': reason
                    })
                
                total_count += 1
    
    elif 'results' in results:
        # Single model batch test format
        model_name = results.get('model', 'unknown')
        
        for result in results['results']:
            qid = result.get('qid')
            correct_answer = result.get('correct_answer')
            prediction = result.get('prediction')
            old_is_correct = result.get('is_correct', False)
            
            if result.get('error'):
                # Skip errors
                continue
            
            # Re-evaluate
            new_is_correct, reason = is_answer_in_range(prediction, correct_answer)
            
            # Update if changed
            if old_is_correct != new_is_correct:
                result['is_correct'] = new_is_correct
                result['_fix_reason'] = reason
                fixed_count += 1
                
                details.append({
                    'qid': qid,
                    'model': model_name,
                    'correct_answer': correct_answer,
                    'prediction': prediction,
                    'old_status': old_is_correct,
                    'new_status': new_is_correct,
                    'reason': reason
                })
            
            total_count += 1
    
    # Recalculate summary statistics
    if 'results' in results:
        # Single model batch format - recalculate accuracy
        correct = sum(1 for r in results['results'] if r.get('is_correct') and not r.get('error'))
        total = sum(1 for r in results['results'] if not r.get('error'))
        
        if 'summary' not in results:
            results['summary'] = {}
        
        results['summary']['correct'] = correct
        results['summary']['total'] = total
        results['summary']['accuracy'] = correct / max(total, 1)
    
    elif 'questions' in results:
        # Comparison format - recalculate for each model
        # Dynamically detect model names
        excluded_keys = {'qid', 'question_text', 'correct_answer', 'topic', 'question_type'}
        sample_question = results['questions'][0] if results['questions'] else {}
        model_names = [key for key in sample_question.keys() if key not in excluded_keys]
        
        if 'summary' not in results:
            results['summary'] = {}
        
        for model_name in model_names:
            correct_count = sum(1 for q in results['questions'] 
                              if q.get(model_name, {}).get('success') 
                              and q[model_name].get('is_correct'))
            total_count = sum(1 for q in results['questions'] 
                             if q.get(model_name, {}).get('success'))
            
            if model_name not in results['summary']:
                results['summary'][model_name] = {}
            
            results['summary'][model_name]['correct'] = correct_count
            results['summary'][model_name]['total'] = total_count
            results['summary'][model_name]['accuracy'] = correct_count / max(total_count, 1)
    
    # Save results
    output_path = Path(output_file) if output_file else input_path
    print(f"\nSaving corrected results to: {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("CORRECTION SUMMARY")
    print("="*80)
    print(f"Total questions evaluated: {total_count}")
    print(f"Corrections made: {fixed_count}")
    
    if 'summary' in results:
        if 'results' in results:
            # Single model format
            summary = results['summary']
            print(f"Final accuracy: {summary.get('accuracy', 0)*100:.2f}% ({summary.get('correct', 0)}/{summary.get('total', 0)})")
        else:
            # Comparison format - print all models in summary
            for model_name, summary in results['summary'].items():
                if isinstance(summary, dict) and 'accuracy' in summary:
                    print(f"\n{model_name}:")
                    print(f"  Final accuracy: {summary['accuracy']*100:.2f}% ({summary['correct']}/{summary['total']})")
    
    # Print detailed changes
    if details:
        print("\n" + "="*80)
        print("DETAILED CHANGES")
        print("="*80)
        
        for detail in details:
            print(f"\n[{detail['qid']}] {detail['model']}")
            if 'question' in detail:
                print(f"  Question: {detail['question']}")
            print(f"  Correct Answer: {detail['correct_answer']}")
            print(f"  Prediction: {detail['prediction']}")
            print(f"  Status: {detail['old_status']} → {detail['new_status']}")
            print(f"  Reason: {detail['reason']}")
    
    print("\n" + "="*80)
    print(f"✓ Results saved to: {output_path}")
    print("="*80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix accuracy evaluation for range-based answers in batch test results'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON results file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output file (default: overwrites input)',
        default=None
    )
    
    args = parser.parse_args()
    
    fix_results_file(args.input_file, args.output)


if __name__ == '__main__':
    main()
