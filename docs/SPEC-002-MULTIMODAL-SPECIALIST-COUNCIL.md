# SPEC-002 — Conselho Multimodal de Especialistas com Gemma 4 / LiteRT-LM

Status: implemented in branch  
Versão do contrato: `medical-specialist-council/1.0`

## 1. Objetivo

Adicionar ao projeto um conselho de especialistas virtuais para casos exclusivamente sintéticos, com:

- interpretação multimodal delegável a um runtime local LiteRT-LM/Gemma 4;
- rodada independente por especialidade;
- validação cruzada por claims estruturados;
- agregação inspirada no produto de Nash, sem votação majoritária ingênua;
- auditoria adversarial e incerteza explícita;
- integração com o Medical Digital Twin;
- execução pelo OpenCode CLI.

## 2. Não objetivos

O sistema não pode:

- diagnosticar uma pessoa real;
- prescrever medicamentos, doses, dietas ou exercícios;
- selecionar procedimento invasivo;
- assinar laudo ou substituir especialista habilitado;
- converter consenso entre modelos em verdade clínica;
- aceitar imagens ou arquivos fora do worktree;
- executar comando LiteRT-LM fornecido pelo prompt.

## 3. Atores

- `medical-council-coordinator`: coordena rodadas e artefatos.
- `internal_medicine`: integra contexto clínico sintético.
- `radiology`: descreve limitações e observações visuais não diagnósticas.
- `pharmacology`: identifica perguntas de segurança farmacológica.
- `procedures`: organiza indicação, contraindicação e pré-requisitos como questões.
- `nutrition`: organiza hipóteses nutricionais educacionais.
- `exercise`: organiza hipóteses funcionais educacionais.
- `methodology`: audita validade, vieses e extrapolação.
- `reversa`: bloqueia excesso de confiança, causalidade indevida e linguagem prescritiva.

## 4. Contratos

Cada especialista produz observações, claims, itens críticos, dados faltantes, perguntas de intervenção, limitações, confiança e força de evidência. O resultado do conselho inclui ID estável, opiniões, matriz de validação cruzada, pesos normalizados, síntese, twin vinculado, gates e parâmetros de reprodução.

## 5. Validação cruzada

1. congelar a primeira opinião de cada especialista;
2. comparar claims por `claim_id`;
3. registrar suporte, oposição e incerteza;
4. calcular concordância par a par;
5. preservar dissenso relevante;
6. nunca apagar opinião minoritária apenas por peso.

## 6. Teoria dos jogos

O peso usa média geométrica de calibração, relevância, força de evidência, confiança, completude e independência. O método é denominado `nash-product-inspired`, não “equilíbrio de Nash clínico”.

## 7. Segurança multimodal

- somente PNG, JPEG e WEBP;
- máximo de 10 imagens;
- máximo de 20 MiB por imagem;
- imagens dentro do worktree;
- adapter hermético não interpreta pixels;
- LiteRT-LM exige `LITERT_LM_COMMAND` administrativo;
- imagem precede texto no payload;
- saída JSON estruturada e validada.

## 8. Critérios de aceitação

- AC-001: caso não sintético é recusado.
- AC-002: caminho externo é recusado.
- AC-003: extensão não permitida é recusada.
- AC-004: mesma entrada e seed produzem mesmo `council_id`.
- AC-005: pesos somam 1.
- AC-006: evidência menor reduz peso, mantidas as demais variáveis.
- AC-007: suporte e oposição geram claim contestado.
- AC-008: dissenso permanece no artefato.
- AC-009: resultado inclui twin `simulation_only`.
- AC-010: diagnóstico, prognóstico e prescrição permanecem bloqueados.
- AC-011: LiteRT-LM sem configuração é bloqueado.
- AC-012: comando do modelo não vem do usuário.
- AC-013: saída inválida do modelo é recusada.
- AC-014: OpenCode separa modo hermético e Gemma.
- AC-015: suíte hermética não chama rede ou modelo.

## 9. Ordem SDD/TDD

1. SPEC e schemas.
2. testes RED dos contratos e invariantes.
3. dataclasses e adapters mínimos.
4. validação cruzada e pesos.
5. integração com o twin.
6. bridge OpenCode.
7. adapter LiteRT-LM.
8. documentação e regressão.
