import { McpServer } from '@modelcontextprotocol/server';
import { createMcpHandler } from 'agents/mcp/server';
import { env } from 'cloudflare:workers';
import { z } from 'zod';

// NÃO há endpoints de escrita: somente consulta a registros revisados.
function settings() {
  const base = (env.SUPABASE_URL || '').replace(/\/$/, '');
  const key = env.SUPABASE_PUBLISHABLE_KEY || '';
  if (!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(base) || !key.startsWith('sb_publishable_')) {
    throw new Error('Supabase não configurado: SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY');
  }
  return { base, key };
}
async function supaQuery(params) {
  const { base, key } = settings();
  const url = new URL(base + '/rest/v1/legal_norm_versions');
  for (const [k,v] of Object.entries(params)) url.searchParams.set(k, String(v));
  url.searchParams.set('publication_state','eq.published');
  const res = await fetch(url, {headers:{'apikey':key,'Accept':'application/json'}, redirect:'manual'});
  // Cloudflare Workers não suporta redirect: 'error'. Nunca seguir redirecionamentos da API jurídica.
  if (res.status >= 300 && res.status < 400) {
    throw new Error('Redirecionamento inesperado do Supabase (HTTP ' + res.status + '). Consulta interrompida por segurança.');
  }
  if (!res.ok) throw new Error('Consulta Supabase indisponível (HTTP '+res.status+')');
  return res.json();
}
function textResult(data){return {content:[{type:'text',text:JSON.stringify(data,null,2)}]};}
function errorResult(err){return {isError:true,content:[{type:'text',text:err instanceof Error ? err.message : 'Erro de consulta'}]};}
function fields(){return 'record_id,document_key,version,norm_type,norm_number,title,summary,official_url,reference_label,verified_excerpt,source_snapshot_sha256,retrieved_on,published_on,effective_from,effective_until,applicability,reviewed_by,reviewed_at,review_pr_url,created_at';}

function createServer(){
  const server=new McpServer({name:'rtc-consulta-juridica',version:'0.1.0'});
  server.registerTool('buscar_referencias_aprovadas',{
    description:'Pesquisa SOMENTE referências legais aprovadas e versionadas sobre IBS/CBS/IS. NÃO verifica fontes na web em tempo real, nem assegura vigência atual sem rechecagem. Retorna URLs oficiais, dispositivos e data da revisão. Quando houver data_operacao, filtra o intervalo de efeitos declarado.',
    inputSchema:z.object({consulta:z.string().min(3).max(200),data_operacao:z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional()})
  },async ({consulta,data_operacao})=>{
    try {
      const tokens=consulta.toLocaleLowerCase('pt-BR').replace(/[^\p{L}\p{N}\s]/gu,' ').trim().split(/\s+/).filter(w=>w.length>=2).slice(0,6);
      if(!tokens.length) return textResult({registros:[],aviso:'Informe termos de pesquisa mais específicos.'});
      const params={select:fields(),search_vector:'fts(portuguese).'+tokens.join(' & '),order:'reviewed_at.desc',limit:5};
      if(data_operacao){
        // Data é validada pela regex acima; conserva registro com intervalo de efeitos.
        params.and=`(effective_from.lte.${data_operacao},or(effective_until.is.null,effective_until.gt.${data_operacao}))`;
      }
      const result=await supaQuery(params);
      return textResult({registros:result,total_retornado:result.length,
        aviso:'Base revisada, não necessariamente atual na data da consulta. Confira atos supervenientes nas fontes oficiais; não confunda data da publicação com efeitos.'});
    } catch(err) {return errorResult(err);}
  });
  server.registerTool('obter_referencia_aprovada',{
    description:'Busca pelo ID exato uma versão aprovada de ato normativo e devolve seu dispositivo, URL, datas e responsável pela revisão.',
    inputSchema:z.object({record_id:z.string().regex(/^[a-z0-9][a-z0-9_.-]{5,90}$/)})
  },async ({record_id})=>{
    try {
      const rows=await supaQuery({select:fields(),record_id:'eq.'+record_id,limit:1});
      return textResult({registro:rows[0]??null,observacao:'Somente registros publicados são visíveis.'});
    } catch(err) {return errorResult(err);}
  });
  server.registerTool('status_base_verificada',{
    description:'Informa a data da revisão mais recente cadastrada. Não significa que houve atualização jurídica em tempo real.',
    inputSchema:z.object({})
  },async ()=>{
    try {
      const rows=await supaQuery({select:'record_id,reviewed_at,retrieved_on,official_url',order:'reviewed_at.desc',limit:1});
      return textResult({ultimo_registro:rows[0]??null,consultado_em:new Date().toISOString(),
       aviso:'Se não houver registros, a base ainda está vazia; nenhuma referência pode ser tratada como comprovada via MCP.'});
    } catch(err) {return errorResult(err);}
  });
  return server;
}
const handler=createMcpHandler(createServer,{responseMode:'json'});
export default {
  fetch(request,context,ctx){
    const url=new URL(request.url);
    if (url.pathname==='/health') return new Response(JSON.stringify({ok:true,component:'rtc-mcp',note:'Health não valida Supabase ou vigência jurídica.'}), {headers:{'Content-Type':'application/json'}});
    return handler(request,context,ctx);
  }
};
