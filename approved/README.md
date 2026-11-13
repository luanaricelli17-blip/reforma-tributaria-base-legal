# Registros jurídicos aprovados

Esta pasta é a única fonte de arquivos `*.record.json` que podem ser publicados no Supabase. Inicialmente não contém registros aprovados.

Fluxo obrigatório:
1. Monitorar fontes oficiais e abrir PR de sinais de alteração (não são atos validados).
2. Conferir manualmente o texto oficial, artigo, parágrafo, data da publicação, vigência e início de efeitos.
3. Criar um PR separado com o arquivo `approved/<id>.record.json`, contendo referência, URL oficial, hash de fonte e identificação do revisor.
4. Conferir também a alteração de código e o comportamento de GitHub Actions; a chave `SUPABASE_SECRET_KEY` pode publicar dados quando o PR entrar na branch `main`.
5. Só após revisão jurídica e técnica, fazer merge. O workflow de publicação executa validação estrutural e escreve no Supabase.
6. Nunca alterar uma versão publicada; criar outra versão. Uma referência incorreta deve ser retirada de forma auditável.

Um esquema válido ou um PR aprovado NÃO prova a correção do conteúdo jurídico. Não use exemplos ou placeholders em produção.
