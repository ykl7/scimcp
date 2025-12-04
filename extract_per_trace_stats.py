#!/usr/bin/env python
"""
Extract per-trace (per-question) statistics from Phoenix telemetry database
Each trace corresponds to one question in batch testing

Usage:
    python extract_per_trace_stats.py --project phi4-batch-final
    python extract_per_trace_stats.py --project phi4mini_inst-batch-test -o phi4mini_traces.json
    python extract_per_trace_stats.py --db ~/.phoenix/phoenix.db --project phi4-batch-final
    python extract_per_trace_stats.py --list-projects
"""

import sqlite3
import json
import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def extract_per_trace_stats(db_path, project_name, output_file=None):
    """Extract per-trace statistics for a project"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 100)
    print("PER-TRACE (PER-QUESTION) STATISTICS")
    print("=" * 100)
    print(f"Database: {db_path}")
    print(f"Project:  {project_name}")
    
    # Get all traces for this project
    cursor.execute("""
        SELECT rowid, trace_id, start_time, end_time
        FROM traces 
        WHERE project_name = ?
        ORDER BY start_time
    """, (project_name,))
    
    traces = cursor.fetchall()
    
    if not traces:
        print(f"\nNo traces found for project '{project_name}'")
        cursor.execute("""
            SELECT project_name, COUNT(*) as cnt 
            FROM traces 
            WHERE project_name IS NOT NULL
            GROUP BY project_name
        """)
        print("\nAvailable projects:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} traces")
        conn.close()
        return None
    
    print(f"Found {len(traces)} traces\n")
    
    trace_stats = []
    
    for idx, (trace_rowid, trace_id, start_time, end_time) in enumerate(traces, 1):
        # Get token counts from spans
        cursor.execute("""
            SELECT 
                MAX(cumulative_llm_token_count_prompt) as prompt_tokens,
                MAX(cumulative_llm_token_count_completion) as completion_tokens
            FROM spans
            WHERE trace_rowid = ?
        """, (trace_rowid,))
        token_row = cursor.fetchone()
        prompt_tokens = token_row[0] or 0
        completion_tokens = token_row[1] or 0
        
        # Count LLM calls
        cursor.execute("""
            SELECT COUNT(*) FROM spans
            WHERE trace_rowid = ? AND span_kind = 'LLM'
        """, (trace_rowid,))
        llm_calls = cursor.fetchone()[0]
        
        # Count tool calls and get tool names
        cursor.execute("""
            SELECT attributes FROM spans
            WHERE trace_rowid = ? 
            AND (span_kind = 'TOOL' OR name LIKE '%Tool%')
        """, (trace_rowid,))
        
        tools_used = []
        tool_call_count = 0
        for row in cursor.fetchall():
            try:
                attrs = json.loads(row[0])
                tool_name = attrs.get('tool.name') or attrs.get('name')
                if tool_name and tool_name != 'final_answer':
                    tools_used.append(tool_name)
                    tool_call_count += 1
            except:
                pass
        
        # Count total spans (approximates steps)
        cursor.execute("""
            SELECT COUNT(*) FROM spans WHERE trace_rowid = ?
        """, (trace_rowid,))
        total_spans = cursor.fetchone()[0]
        
        # Count agent steps specifically
        cursor.execute("""
            SELECT COUNT(*) FROM spans 
            WHERE trace_rowid = ? AND name LIKE 'Step %'
        """, (trace_rowid,))
        agent_steps = cursor.fetchone()[0]
        
        # Calculate duration
        cursor.execute("""
            SELECT 
                MIN(start_time), 
                MAX(end_time),
                (julianday(MAX(end_time)) - julianday(MIN(start_time))) * 86400 as duration_sec
            FROM spans
            WHERE trace_rowid = ?
        """, (trace_rowid,))
        time_row = cursor.fetchone()
        duration_sec = time_row[2] or 0
        
        # Check for errors
        cursor.execute("""
            SELECT COUNT(*) FROM spans 
            WHERE trace_rowid = ? AND status_code = 'ERROR'
        """, (trace_rowid,))
        error_count = cursor.fetchone()[0]
        
        trace_stats.append({
            'trace_num': idx,
            'trace_id': trace_id,
            'tokens_prompt': int(prompt_tokens),
            'tokens_completion': int(completion_tokens),
            'tokens_total': int(prompt_tokens + completion_tokens),
            'llm_calls': llm_calls,
            'tool_calls': tool_call_count,
            'tools_used': list(set(tools_used)),  # unique tools
            'agent_steps': agent_steps,
            'total_spans': total_spans,
            'duration_sec': round(duration_sec, 2),
            'has_error': error_count > 0
        })
        
        # Progress indicator
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(traces)} traces...")
    
    conn.close()
    
    # Print summary table (first 20)
    print(f"\n{'#':<5s} {'Tokens':>10s} {'LLM':>6s} {'Tools':>6s} {'Steps':>6s} {'Time':>8s} {'Status':<8s}")
    print("-" * 60)
    
    for stat in trace_stats[:20]:
        status = "ERROR" if stat['has_error'] else "OK"
        print(f"{stat['trace_num']:<5d} "
              f"{stat['tokens_total']:>10,d} "
              f"{stat['llm_calls']:>6d} "
              f"{stat['tool_calls']:>6d} "
              f"{stat['agent_steps']:>6d} "
              f"{stat['duration_sec']:>7.1f}s "
              f"{status:<8s}")
    
    if len(trace_stats) > 20:
        print(f"... and {len(trace_stats) - 20} more traces")
    
    # Aggregated statistics
    print("\n" + "=" * 100)
    print("AGGREGATED STATISTICS")
    print("=" * 100)
    
    total_traces = len(trace_stats)
    total_tokens = sum(s['tokens_total'] for s in trace_stats)
    total_tool_calls = sum(s['tool_calls'] for s in trace_stats)
    total_llm_calls = sum(s['llm_calls'] for s in trace_stats)
    total_steps = sum(s['agent_steps'] for s in trace_stats)
    total_duration = sum(s['duration_sec'] for s in trace_stats)
    errors = sum(1 for s in trace_stats if s['has_error'])
    
    print(f"\nTotal Traces:        {total_traces}")
    print(f"Total Tokens:        {total_tokens:,}")
    print(f"Total LLM Calls:     {total_llm_calls:,}")
    print(f"Total Tool Calls:    {total_tool_calls:,}")
    print(f"Total Agent Steps:   {total_steps:,}")
    print(f"Total Duration:      {total_duration:,.1f}s ({total_duration/3600:.2f} hours)")
    print(f"Errors:              {errors}")
    
    print(f"\nAverages per Trace:")
    print(f"  Tokens:            {total_tokens/total_traces:,.0f}")
    print(f"  LLM Calls:         {total_llm_calls/total_traces:.1f}")
    print(f"  Tool Calls:        {total_tool_calls/total_traces:.1f}")
    print(f"  Agent Steps:       {total_steps/total_traces:.1f}")
    print(f"  Duration:          {total_duration/total_traces:.1f}s")
    
    # Tool usage breakdown
    all_tools = defaultdict(int)
    for stat in trace_stats:
        for tool in stat['tools_used']:
            all_tools[tool] += 1
    
    print(f"\nTop 10 Tools Used:")
    for tool, count in sorted(all_tools.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {tool:45s}: {count:4d} traces")
    
    # Save to JSON
    if output_file:
        output_data = {
            'project': project_name,
            'total_traces': total_traces,
            'summary': {
                'total_tokens': total_tokens,
                'total_llm_calls': total_llm_calls,
                'total_tool_calls': total_tool_calls,
                'total_steps': total_steps,
                'total_duration_sec': total_duration,
                'errors': errors,
                'avg_tokens_per_trace': total_tokens / total_traces,
                'avg_llm_calls_per_trace': total_llm_calls / total_traces,
                'avg_tool_calls_per_trace': total_tool_calls / total_traces,
                'avg_steps_per_trace': total_steps / total_traces,
                'avg_duration_per_trace': total_duration / total_traces
            },
            'tool_usage': dict(sorted(all_tools.items(), key=lambda x: x[1], reverse=True)),
            'traces': trace_stats
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n✅ Detailed stats saved to: {output_file}")
    
    print("\n" + "=" * 100)
    
    return trace_stats


def main():
    parser = argparse.ArgumentParser(
        description='Extract per-trace (per-question) statistics from Phoenix database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_per_trace_stats.py --list-projects
  python extract_per_trace_stats.py --project phi4-batch-final
  python extract_per_trace_stats.py --project phi4-batch-final -o phi4_traces.json
  python extract_per_trace_stats.py --project phi4mini_inst-batch-test -o phi4mini_traces.json
        """
    )
    parser.add_argument(
        '--db', '-d',
        default=None,
        help='Path to Phoenix database (default: ~/.phoenix/phoenix.db)'
    )
    parser.add_argument(
        '--project', '-p',
        default=None,
        help='Project name to extract stats for (required unless --list-projects)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output JSON file for detailed per-trace stats'
    )
    parser.add_argument(
        '--list-projects',
        action='store_true',
        help='List available projects and exit'
    )
    
    args = parser.parse_args()
    
    # Determine database path
    if args.db:
        db_path = args.db
    else:
        home = Path.home()
        possible_paths = [
            home / '.phoenix' / 'phoenix.db',
            Path('/home/yaswanthreddy/.phoenix/phoenix.db'),
        ]
        db_path = None
        for p in possible_paths:
            if p.exists():
                db_path = str(p)
                break
        
        if not db_path:
            print("Error: Could not find Phoenix database. Use --db to specify path.")
            return
    
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    if args.list_projects:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_name, COUNT(*) as trace_count 
            FROM traces 
            WHERE project_name IS NOT NULL
            GROUP BY project_name
            ORDER BY trace_count DESC
        """)
        print(f"\nProjects in {db_path}:")
        print("-" * 60)
        print(f"{'Project Name':<45s} {'Traces':>10s}")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]:<43s}: {row[1]:>8d}")
        conn.close()
        return
    
    if not args.project:
        print("Error: --project is required. Use --list-projects to see available projects.")
        return
    
    extract_per_trace_stats(db_path, args.project, args.output)


if __name__ == "__main__":
    main()
