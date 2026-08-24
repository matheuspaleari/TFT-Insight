import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a,composition_a_variant,composition_b
from src.decision_engine.analyzers.composition_analyzer import CompositionAnalyzer
from src.decision_engine.analyzers.composition_similarity_analyzer import CompositionSimilarityAnalyzer
from src.decision_engine.analyzers.composition_cluster_analyzer import CompositionClusterAnalyzer
a=CompositionAnalyzer.analyze(composition_a("A1",2))
av=CompositionAnalyzer.analyze(composition_a_variant("A2",3))
b=CompositionAnalyzer.analyze(composition_b("B1",5))
same=CompositionSimilarityAnalyzer.compare(a,av)
other=CompositionSimilarityAnalyzer.compare(a,b)
clusters=CompositionClusterAnalyzer.cluster((a,av,b))
checks=[
("Variante semelhante > diferente",same.score>other.score),
("Variante acima threshold",same.score>=55),
("Composição diferente abaixo threshold",other.score<55),
("Forma 2 clusters",len(clusters)==2),
("Variante agrupada",max(c.matches_played for c in clusters)==2),
]
print("="*92);print("#25.3 - SIMILARITY + CLUSTERING V2");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nSimilar A/A-variante: {same.score}\\nSimilar A/B: {other.score}")
print(f"PASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.3: VALIDADO")
