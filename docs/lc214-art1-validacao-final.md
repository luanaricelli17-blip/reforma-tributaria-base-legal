# Pré-publicação — LC nº 214/2025, art. 1º (IBS e CBS)

**Status:** PENDENTE DE APROVAÇÃO FINAL — **NÃO PUBLICAR NO SUPABASE**.

## Evidências e conferências de 13/11/2026
- Fonte primária: [Lei Complementar nº 214/2025, Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm).
- Fonte de corroboração: [texto atualizado, Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/leicom/2025/leicomplementar-214-16-janeiro-2025-796905-normaatualizada-pl.html).
- Art. 1º, incisos I e II: instituem, respectivamente, IBS (Estados, DF, Municípios) e CBS (União).
- Art. 544, inciso VI: efeitos a partir de 01/01/2026 para os demais dispositivos, incluindo art. 1º. A instituição não corresponde à cobrança integral.
- LC 227/2026 alterou art. 544, III, não o VI neste ponto; LC 235/2026 altera outros dispositivos (82, 174), não o art. 1º.
- A Câmara registra ausência de revogação expressa integral da LC 214/2025 na ficha da norma (não equivale a garantia de ausência de alteração futura).

## Manifestação registrada no PR #8
- [Comentário da revisora indicada, Luana Ricelli de Souza](https://github.com/luanaricelli17-blip/reforma-tributaria-base-legal/pull/8#issuecomment-6856376286), de 13/11/2026.
- O comentário **não autorizou** publicação: deixou pendente confirmar efeitos, alterações e preservar evidências.

## Para aprovação final
1. Salvar evidência fiel do texto atualizado utilizado (PDF oficial/snapshot), identificar versão, data e calcular hash SHA-256 do arquivo preservado. O hash `monitor/state.json` é apenas do conteúdo normalizado da página no dia da coleta.
2. Revisar integralmente a declaração jurídica no arquivo `reviews/lc214-2025-art1-prepublicacao.json` e verificar ajustes posteriores, incluindo eventual republicação.
3. Registrar aprovação expressa da referência delimitada (não da lei inteira), sua data real, responsável e a evidência, num novo PR de publicação.
4. Criar `approved/lc214-2025-art1-v1.record.json` exclusivamente depois da aprovação final. Atenção: qualquer merge desse arquivo pode iniciar `publicar-aprovados.yml` e afetar o Supabase.
5. Validar novamente em teste MCP e verificar a filtragem RLS em leitura anônima; não presumir atualização automática em tempo real.

## Segurança
Nenhum arquivo deste PR está em `approved/`. A ficha preliminar usa campos adicionais que não passam pelo validador de publicações e não deve ser copiada sem saneamento. **Não incluir chaves, identificação pessoal de clientes nem dados fiscais de terceiros no repositório público.**
