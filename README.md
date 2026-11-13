# Reforma Tributária Brasil — base jurídica versionada (projeto gratuito)

Arquitetura: **GitHub Actions (coleta e PR) → revisão jurídica humana → GitHub Actions (publicação) → Supabase RLS (apenas publicados) → Cloudflare Worker MCP (somente leitura) → plugin ChatGPT**.

## Segurança e estado
- A base **não é atualizada automaticamente sem revisão humana**. `monitor/check_sources.py` apenas detecta sinais de mudança nas páginas oficiais; esses sinais não têm força normativa.
- `approved/*.record.json` contém somente registros aprovados após verificação do dispositivo, texto e vigência.
- `sync/validate_records.py` valida estrutura, URL oficial, metadados e hash da página, **não** substitui conferência jurídica.
- `sync/publish_records.py` sincroniza registros aprovados usando segredo administrativo apenas no GitHub Actions, nunca no Cloudflare Worker nem no código do repositório.
- O Worker continua somente de leitura, sempre filtrando `publication_state=eq.published`.
- O SQL em `supabase/schema.sql` exige RLS, SELECT para `anon` apenas em `published` e não permite exclusão do histórico.

## Ativação após aprovação deste PR
1. GitHub → Actions: verifique as rotinas **Coletar mudanças em fontes oficiais**, **Validar revisão antes do merge** e **Publicar somente versões aprovadas**.
2. GitHub → Settings → Actions → General: confira permissões de workflow; se desejar que o coletor proponha PR, permita criação de pull requests pelo GitHub Actions.
3. Teste a coleta por `Actions → Coletar mudanças ... → Run workflow`. Ela abre um PR de **sinais para revisão** e não escreve no Supabase.
4. Configure `SUPABASE_URL` e `SUPABASE_SECRET_KEY` em *GitHub Actions secrets* somente depois de definir quem revisa e aprova os PRs e de confirmar as políticas RLS. **Nunca** compartilhe secret keys em chats ou commits.
5. Para publicar a primeira norma: confirme o texto oficial e a data de efeitos, documente um PR específico com arquivo `approved/<id>.record.json`, confira o hash presente em `monitor/state.json`, registre o revisor e revise o PR antes do merge.
6. Confira a publicação e repita `status_base_verificada`, `buscar_referencias_aprovadas` e `obter_referencia_aprovada` via MCP.

## Diagnóstico SQL no Supabase
```sql
select publication_state, count(*) as quantidade
from public.legal_norm_versions
group by publication_state
order by publication_state;

select record_id, document_key, version, reference_label, official_url, reviewed_at
from public.legal_norm_versions
where publication_state = 'published'
order by reviewed_at desc
limit 10;
```

**Importante:** como o repositório GitHub é público, informações nos arquivos e histórico do Git serão públicas. Não armazene dados fiscais de contribuintes, informações pessoais ou credenciais no código.

## Limitações
O monitor verifica o conteúdo das páginas e pode detectar alterações cosméticas ou ignorar mudanças em documentos vinculados. O revisor precisa ler o ato oficial em si e verificar vigência, revogações e notas técnicas aplicáveis. Supabase Free e Workers Free têm limites e podem ficar indisponíveis. Não há SLA nem garantia de conformidade jurídica automática.
