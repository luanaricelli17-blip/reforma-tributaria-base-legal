-- TESTE REVERSÍVEL: isolamento RLS da tabela public.legal_norm_versions
-- Execute o arquivo INTEIRO no SQL Editor do projeto rtc-conhecimento.
-- A transação termina em ROLLBACK: NENHUM registro de teste será salvo.
-- Não execute partes isoladas, nem substitua ROLLBACK por COMMIT.
BEGIN;

INSERT INTO public.legal_norm_versions (
  record_id, document_key, version, norm_type, norm_number,
  title, summary, official_url, reference_label, verified_excerpt,
  source_id, source_snapshot_sha256, retrieved_on, published_on,
  effective_from, applicability, reviewed_by, reviewed_at,
  review_pr_url, publication_state, withdrawn_at
)
VALUES
(
  'teste-rls-20261113-publicado', 'teste-rls-publicado', 1, 'TESTE', 'RLS-01',
  'TESTE RLS - documento publicado (não jurídico)',
  'Registro inteiramente fictício, criado apenas dentro de transação temporária para testar controle de leitura.',
  'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm',
  'TESTE TÉCNICO - sem aprovação jurídica',
  'Este trecho é exclusivamente fictício, sem validade legal e não deve ser divulgado como dispositivo de lei.',
  'teste-rls', repeat('0',64), current_date, current_date,
  current_date, 'APENAS TESTE', 'TESTE AUTOMATIZADO', now(),
  'https://github.com/luanaricelli17-blip/reforma-tributaria-base-legal/pull/5',
  'published', NULL
),
(
  'teste-rls-20261113-retirado', 'teste-rls-retirado', 1, 'TESTE', 'RLS-02',
  'TESTE RLS - documento retirado (não jurídico)',
  'Registro inteiramente fictício, criado apenas dentro de transação temporária para testar controle de leitura.',
  'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm',
  'TESTE TÉCNICO - sem aprovação jurídica',
  'Este trecho é exclusivamente fictício, sem validade legal e não deve ser divulgado como dispositivo de lei.',
  'teste-rls', repeat('0',64), current_date, current_date,
  current_date, 'APENAS TESTE', 'TESTE AUTOMATIZADO', now(),
  'https://github.com/luanaricelli17-blip/reforma-tributaria-base-legal/pull/5',
  'withdrawn', now()
);

SET LOCAL ROLE anon;
DO $teste_anon$
DECLARE
  publicado integer;
  retirado integer;
BEGIN
  SELECT count(*) INTO publicado FROM public.legal_norm_versions
    WHERE record_id = 'teste-rls-20261113-publicado';
  SELECT count(*) INTO retirado FROM public.legal_norm_versions
    WHERE record_id = 'teste-rls-20261113-retirado';
  IF publicado <> 1 OR retirado <> 0 THEN
    RAISE EXCEPTION 'FALHOU RLS anon: publicado=%, retirado=%', publicado, retirado;
  END IF;
  IF has_table_privilege('anon','public.legal_norm_versions','INSERT,UPDATE,DELETE') THEN
    RAISE EXCEPTION 'FALHOU: anon possui alguma permissão de escrita';
  END IF;
  RAISE NOTICE 'PASSOU anon: publicado visível=1, retirado visível=0, escrita bloqueada';
END
$teste_anon$;

SET LOCAL ROLE authenticated;
DO $teste_auth$
DECLARE
  publicado integer;
  retirado integer;
BEGIN
  SELECT count(*) INTO publicado FROM public.legal_norm_versions
    WHERE record_id = 'teste-rls-20261113-publicado';
  SELECT count(*) INTO retirado FROM public.legal_norm_versions
    WHERE record_id = 'teste-rls-20261113-retirado';
  IF publicado <> 1 OR retirado <> 0 THEN
    RAISE EXCEPTION 'FALHOU RLS authenticated: publicado=%, retirado=%', publicado, retirado;
  END IF;
  IF has_table_privilege('authenticated','public.legal_norm_versions','INSERT,UPDATE,DELETE') THEN
    RAISE EXCEPTION 'FALHOU: authenticated possui alguma permissão de escrita';
  END IF;
  RAISE NOTICE 'PASSOU authenticated: publicado visível=1, retirado visível=0, escrita bloqueada';
END
$teste_auth$;

ROLLBACK;
-- Recomendado: confirme a ausência dos testes executando, em outra consulta:
-- SELECT count(*) FROM public.legal_norm_versions WHERE record_id LIKE 'teste-rls-20261113-%';
