# Validação técnica e jurídica — instruções
Este PR é **somente preparatório**; não autoriza publicar normas jurídicas, não executa SQL no Supabase e não altera o Worker.

## 1. Teste técnico
No Supabase Dashboard → `rtc-conhecimento` → SQL Editor, abra o arquivo `supabase/tests/rls_isolamento_transacao.sql`, clique em **Raw**, copie seu conteúdo **inteiro**, cole em **New query** e execute.

- O teste insere temporariamente 2 registros fictícios (um `published`, outro `withdrawn`), simula as funções `anon` e `authenticated`, e usa **ROLLBACK** para desfazer tudo.
- Se não ocorrer erro, a verificação de visibilidade e permissões passou na sessão SQL (veja as mensagens NOTICE).
- Em outra consulta, confirme: `SELECT count(*) FROM public.legal_norm_versions WHERE record_id LIKE 'teste-rls-20261113-%';` → deve retornar zero.
- Se houver erro: **não** execute COMMIT. Rode `ROLLBACK;` em uma nova consulta e encaminhe a mensagem de erro.
- Não execute uma parte isolada do script e não teste isso em produção com dados reais.

## 2. Revisão da primeira referência legal
O arquivo `reviews/lc214-art1-candidato.json` é apenas candidato: status `PENDENTE_REVISAO_HUMANA_NAO_PUBLICAR`. Não é consumido pelo publicador `sync/publish_records.py`.

Fonte principal: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm
- Dispositivo: art. 1º, incisos I e II — IBS e CBS.
- Art. 544, VI — efeitos a partir de 1º/1/2026 para os dispositivos não incluídos nas hipóteses anteriores.
- Considere a LC 227/2026 e posteriores, texto compilado e demais atos relacionados. A eficácia do art. 1º não define, sozinha, todas as obrigações ou alíquotas da transição.

**Proibição:** Não mover o candidato para `approved/` sem conferência jurídica humana documentada; o hash de página monitorada não equivale a uma cópia verificável do texto vigente.

## 3. Depois dos testes
Registrar resultados de RLS, revisor jurídico e evidência oficial. Em PR separado, propor `approved/*.record.json` com dispositivo e vigência. Somente após aprovação publicar no Supabase e testar MCP.
