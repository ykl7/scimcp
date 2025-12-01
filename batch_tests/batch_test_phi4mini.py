"""
Batch testing script for Phi-4-mini-instruct model only
Can be run in parallel with other model test scripts
"""
import os
import json
import time
import sys
from datetime import datetime
from smolagents import CodeAgent
from smolagents.models import OpenAIServerModel
from smolagents.tools import ToolCollection
from mcp import StdioServerParameters
from smolagents.utils import AgentGenerationError
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

# Setup Phoenix with unique project name for Phi-4-mini-instruct
tracer_provider = register(project_name="phi4mini-batch-test")
SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from Tool_processing.Relevant_tools import get_relevant
from Tools.Mat_Sci_tools import MaterialScienceToolRegistry


def load_mascqa_questions(dataset_path, num_questions=20, topic=None, diverse=True):
    """Load questions from MASCQA dataset"""
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    questions = []
    
    if num_questions == -1:
        # Load all questions
        for topic_name, topic_data in data.items():
            if topic and topic_name != topic:
                continue
            
            qids = topic_data['qids']
            qstr = topic_data['qstr']
            question_texts = topic_data['questions']
            correct_answers = topic_data['correct_answers']
            
            for i in range(len(qids)):
                questions.append({
                    'qid': qids[i],
                    'question_text': question_texts[i],
                    'correct_answer': correct_answers[i],
                    'topic': topic_name,
                    'question_type': qstr[i]
                })
        return questions
    
    if diverse:
        # Sample evenly across topics
        topics_list = list(data.keys()) if not topic else [topic]
        num_per_topic = max(1, num_questions // len(topics_list))
        
        for topic_name in topics_list:
            topic_data = data[topic_name]
            qids = topic_data['qids']
            qstr = topic_data['qstr']
            question_texts = topic_data['questions']
            correct_answers = topic_data['correct_answers']
            
            num_from_topic = min(num_per_topic, len(qids))
            
            for i in range(num_from_topic):
                questions.append({
                    'qid': qids[i],
                    'question_text': question_texts[i],
                    'correct_answer': correct_answers[i],
                    'topic': topic_name,
                    'question_type': qstr[i]
                })
            
            if len(questions) >= num_questions:
                break
    else:
        # Load sequentially
        for topic_name, topic_data in data.items():
            if topic and topic_name != topic:
                continue
            
            qids = topic_data['qids']
            qstr = topic_data['qstr']
            question_texts = topic_data['questions']
            correct_answers = topic_data['correct_answers']
            
            for i in range(len(qids)):
                if len(questions) >= num_questions:
                    break
                
                questions.append({
                    'qid': qids[i],
                    'question_text': question_texts[i],
                    'correct_answer': correct_answers[i],
                    'topic': topic_name,
                    'question_type': qstr[i]
                })
            
            if len(questions) >= num_questions:
                break
    
    return questions[:num_questions]


def test_mascqa_with_phi4mini(question_text, correct_answer, model, all_tools, all_toolnames):
    """Test a single MASCQA question with Phi-4-mini-instruct"""
    custom_instructions = """
You are a materials science expert tasked with answering questions accurately.

MANDATORY TOOL USAGE RULES:
1. For ANY formula, equation, or calculation → MUST use tools to verify/lookup
2. For material properties (band gap, density, crystal structure, etc.) → MUST use Materials Project tools
3. For definitions, theories, or fundamental concepts → MUST use Wikipedia or research paper tools
4. For claims requiring evidence or citations → MUST use Semantic Scholar, ArXiv, or Ar5iv tools
5. For proofs or derivations → MUST search for authoritative sources using paper search tools

You MAY use your knowledge for:
- Basic logical deduction and reasoning
- Comparing retrieved information
- Synthesizing evidence from multiple tool results
- Drawing conclusions from verified data

WORKFLOW:
1. Analyze what information is needed (formulas? properties? definitions? evidence?)
2. Use appropriate tools to gather that information
3. Verify the retrieved information is relevant
4. Apply reasoning to synthesize a final answer

Do NOT rely solely on your parametric knowledge for factual claims, formulas, or material properties.
IMPORTANT: Always use tools to gather evidence - do NOT verify claims using only parametric knowledge and include final answer in a new step.
    """
    try:
        # Filter tools
        relevant_tools = get_relevant(query=question_text, toolnames=all_toolnames)
        filtered_tools = [t for t in all_tools if t.name in relevant_tools]
        
        print(f"     Tools: {len(filtered_tools)} selected from {len(all_tools)} available")
        
        # Create agent (Phi-4-mini without planning)
        agent = CodeAgent(
            tools=filtered_tools,
            model=model,
            additional_authorized_imports=['json', 're', 'math'],
            planning_interval=0,  # No planning for Phi-4-mini
            instructions=custom_instructions,
            use_structured_outputs_internally=False,
            max_steps=15
        )
        
        # Run query
        query_with_prompt = f"{question_text}\n\nIMPORTANT: Provide your final answer clearly. If it's a multiple choice question, state the option letter (A, B, C, or D). If it's a numerical question, provide the numerical value."
        
        start_time = time.time()
        result = agent.run(query_with_prompt)
        duration = time.time() - start_time
        
        # Extract answer
        result_str = str(result)
        prediction = result_str.strip()
        
        # Check correctness
        correct_answer_str = str(correct_answer).strip()
        is_correct = correct_answer_str.lower() in prediction.lower()
        
        # Count steps
        num_steps = len(agent.step_summaries) if hasattr(agent, 'step_summaries') else 0
        
        return {
            'success': True,
            'prediction': prediction,
            'is_correct': is_correct,
            'result': result_str,
            'duration': duration,
            'steps': num_steps,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'prediction': None,
            'is_correct': False,
            'result': None,
            'duration': None,
            'steps': None,
            'error': str(e)
        }


def run_batch_test_mascqa(questions, output_file='batch_test_phi4mini_results.json'):
    """Run batch testing on MASCQA questions with Phi-4-mini-instruct"""
    
    # Initialize model
    phi4mini = OpenAIServerModel(
        model_id="Phi-4-mini-instruct",
        api_base="https://sbu-all.services.ai.azure.com/openai/v1/",
        api_key=os.getenv("AZURE_API_KEY"),
    )
    
    # Setup MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["MCP/server.py"],
        env={**os.environ}
    )
    
    # Load existing results if available
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing_results = json.load(f)
        print(f"Found existing results file: {output_file}")
        print(f"Already completed: {len(existing_results['results'])} questions")
        completed_qids = set(r['qid'] for r in existing_results['results'])
        
        # Filter out completed questions
        questions = [q for q in questions if q['qid'] not in completed_qids]
        if not questions:
            print("All questions already completed!")
            return existing_results
        print(f"Resuming from question {len(completed_qids) + 1}...")
    else:
        existing_results = {
            'model': 'Phi-4-mini-instruct',
            'dataset': 'MASCQA',
            'total_questions': len(questions),
            'results': [],
            'summary': {}
        }
        completed_qids = set()
    
    print(f"\n{'='*80}")
    print(f"BATCH TESTING: {len(questions)} questions from MASCQA dataset")
    print(f"Model: Phi-4-mini-instruct")
    print(f"{'='*80}\n")
    
    with ToolCollection.from_mcp(server_params, trust_remote_code=True, structured_output=True) as tool_collection:
        all_tools = tool_collection.tools
        all_toolnames = [t.name for t in all_tools]
        
        for idx, question in enumerate(questions, start=len(completed_qids) + 1):
            print(f"[{idx}/{len(questions) + len(completed_qids)}] Testing: {question['qid']}")
            print(f"Topic: {question['topic']} | Type: {question['question_type']}")
            print(f"Correct Answer: {question['correct_answer']}")
            print(f"Question: {question['question_text'][:100]}...\n")
            
            print(f"  → Testing with Phi-4-mini-instruct...")
            result = test_mascqa_with_phi4mini(
                question['question_text'],
                question['correct_answer'],
                phi4mini,
                all_tools,
                all_toolnames
            )
            
            if result['success']:
                print(f"     ✓ Answer: {result['prediction'][:50]}...")
                print(f"     {'✓ CORRECT' if result['is_correct'] else '✗ INCORRECT'}")
                print(f"     Duration: {result['duration']:.1f}s | Steps: {result['steps']}\n")
            else:
                print(f"     ✗ Error: {result['error']}\n")
            
            # Save result
            existing_results['results'].append({
                'qid': question['qid'],
                'topic': question['topic'],
                'question_type': question['question_type'],
                'correct_answer': question['correct_answer'],
                'prediction': result['prediction'],
                'is_correct': result['is_correct'],
                'duration': result['duration'],
                'steps': result['steps'],
                'error': result['error']
            })
            
            # Save after each question
            with open(output_file, 'w') as f:
                json.dump(existing_results, f, indent=2)
            print(f"  → Progress saved to {output_file}\n")    # Calculate summary statistics
    results = existing_results['results']
    correct_count = sum(1 for r in results if r['is_correct'])
    total_count = len(results)
    avg_duration = sum(r['duration'] for r in results if r['duration']) / total_count if total_count > 0 else 0
    
    existing_results['summary'] = {
        'total_questions': total_count,
        'correct': correct_count,
        'accuracy': correct_count / total_count if total_count > 0 else 0,
        'avg_duration': avg_duration
    }
    
    # Final save
    with open(output_file, 'w') as f:
        json.dump(existing_results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS - Phi-4-mini-instruct")
    print(f"{'='*80}")
    print(f"Accuracy: {existing_results['summary']['accuracy']*100:.1f}% ({correct_count}/{total_count})")
    print(f"Avg Duration: {avg_duration:.1f}s")
    print(f"{'='*80}\n")
    
    return existing_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch test Phi-4-mini-instruct on MASCQA dataset')
    parser.add_argument('--num', type=int, default=20, help='Number of questions to test (-1 for all)')
    parser.add_argument('--topic', type=str, default=None, help='Specific topic to test')
    parser.add_argument('--diverse', action='store_true', default=True, help='Sample evenly across topics')
    parser.add_argument('--output', type=str, default='batch_test_phi4mini_mascqa_results.json', help='Output file path')
    
    args = parser.parse_args()
    
    # Load questions
    dataset_path = 'data/honeycomb_data/mascqa/mascqa-eval-with_answer.json'
    questions = load_mascqa_questions(dataset_path, num_questions=args.num, topic=args.topic, diverse=args.diverse)
    
    print(f"\n{'='*80}")
    print(f"TESTING MASCQA DATASET - Phi-4-mini-instruct")
    print(f"{'='*80}\n")
    print(f"Loaded {len(questions)} questions from {dataset_path}\n")
    
    # Show topic distribution
    from collections import Counter
    topic_dist = Counter(q['topic'] for q in questions)
    print("Question topics distribution:")
    for topic, count in topic_dist.items():
        print(f"  {topic}: {count}")
    
    # Run batch test
    run_batch_test_mascqa(questions, output_file=args.output)


if __name__ == "__main__":
    main()
