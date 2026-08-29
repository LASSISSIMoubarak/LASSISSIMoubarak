#!/usr/bin/env python3
"""
Post-process quick_projects.csv to produce a final classification and badges.
"""
import csv
import json
import os

IN_FILE = 'quick_projects.csv'
OUT_FILE = 'projects_classification_final.csv'

CATEGORY_MAP = {
    'LLM': 'LLM',
    'Statistiques': 'Statistiques',
    'Biostatistiques': 'Biostatistiques',
    'SparkBigData': 'SparkBigData',
    'Flask': 'Flask',
    'NLP': 'NLP',
    'Image': 'Image',
    'Reinforcement Learning': 'Reinforcement Learning',
    'Dashboard/BI': 'Dashboard/BI',
    'R': 'R',
    'SQL': 'SQL',
}


def badge_for(category):
    if category == 'Unknown':
        return '⚪ Unknown'
    icons = {
        'LLM': '🧠 LLM',
        'Statistiques': '📊 Statistiques',
        'Biostatistiques': '🧬 Biostatistiques',
        'SparkBigData': '☁️ Spark/BigData',
        'Flask': '🌐 Flask',
        'NLP': '🗣️ NLP',
        'Image': '🖼️ Image',
        'Reinforcement Learning': '🎮 RL',
        'Dashboard/BI': '📈 BI',
        'R': '📐 R',
        'SQL': '🗄️ SQL',
    }
    return icons.get(category, category)


def main():
    if not os.path.exists(IN_FILE):
        print('Input file', IN_FILE, 'not found. Run quick scanner first.')
        return

    rows = []
    with open(IN_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            cat = r['category']
            # normalize category
            norm = CATEGORY_MAP.get(cat, 'Unknown')
            badge = badge_for(norm)
            # try to extract top alternative from scores_json
            try:
                scores = json.loads(r.get('scores_json', r.get('scores', '{}')))
            except Exception:
                scores = {}
            rows.append({
                'project': r['project'],
                'path': r['path'],
                'category': norm,
                'score': r.get('score', ''),
                'badge': badge,
                'scores_json': json.dumps(scores, ensure_ascii=False)
            })

    with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['project', 'path', 'category', 'score', 'badge', 'scores_json'])
        for r in rows:
            writer.writerow([r['project'], r['path'], r['category'], r['score'], r['badge'], r['scores_json']])

    print('Wrote', OUT_FILE)


if __name__ == '__main__':
    main()
