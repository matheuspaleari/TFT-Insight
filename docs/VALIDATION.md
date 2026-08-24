# Validação oficial do TFT Insight

A Roadmap 24 consolida as verificações do projeto em um único entrypoint:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile quick
```

## Perfil `quick`

Use durante desenvolvimento e antes de commits pequenos.

Ele verifica:

- presença dos entrypoints e arquivos públicos críticos;
- sintaxe de todos os arquivos Python;
- imports da plataforma, navegação, Home, análise e API;
- `test_platform_imports.py`;
- `test_platform_import_graph.py`;
- `test_session_import_graph.py`.

Comando:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile quick
```

## Perfil `full`

Use antes de release, mudanças estruturais ou publicação do repositório.

Além do perfil quick, executa os contratos consolidados:

- Roadmap 23 / Landing + Home (`validate_48v2_roadmap23_final.py`);
- contrato público do repositório (`validate_49_roadmap24_public_contract.py`);
- smoke test pós-limpeza (`validate_50f_v4_roadmap24_smoke_after_cleanup.py`).

Comando:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile full
```

## Guardrails

Quando quiser incluir a auditoria geral de guardrails no fluxo completo:

```powershell
python scripts\validate_51_roadmap24_official_suite.py --profile full --guardrails
```

A opção é separada porque a auditoria de guardrails pode ser mais demorada e possuir critérios próprios de revisão.

## Política

A suíte oficial não substitui diagnósticos específicos durante desenvolvimento.

Ela define o conjunto mínimo e consolidado para responder:

> A camada pública do TFT Insight continua íntegra depois desta mudança?

Scripts históricos podem permanecer em `scripts/archive/`, mas não precisam fazer parte do caminho oficial de validação.
