# Operações da Viktrine

Somente administradores podem enviar/importar arquivos, consultar relatórios ou checar links. Os eventos e campos novos usam a autorização administrativa existente; esconder botões não é o controle de acesso.

## CSV: procedimento e modelos

1. Selecione o tipo no painel e baixe seu cabeçalho. Um arquivo por tipo, somente inserções. Não há atualização por ID nem sobrescrita.
2. Use UTF-8, com BOM opcional, vírgula como separador. Até 512 KiB e 100 registros. Campos que contêm vírgula, aspas ou quebra de linha devem ser delimitados por aspas; aspas internas são duplicadas. Colunas duplicadas, desconhecidas, células ausentes e excesso de células são recusados.
3. Envie pelo upload Reflex. O arquivo é lido com limite, não é disponibilizado publicamente nem arquivado como download. A prévia fica apenas na sessão administrativa; não constitui persistência.
4. Confira erros por número de registro (cabeçalho = registro 1). A prévia mostra até 20 registros, mas valida todos. A prévia não grava registros, auditorias ou candidatos a duplicados.
5. Informe motivo e confirme explicitamente. Todo o lote é revalidado em uma transação com auditoria individual. Se qualquer registro falhar, o lote inteiro é revertido; envie novamente para nova prévia. Dependências devem existir antes do lote e não podem ser referências a outros registros do mesmo arquivo.
6. Consulte os IDs confirmados e revise na curadoria. Produtos, variantes, ofertas, lojas e programas importados ficam `draft`; links ficam `pending`. Categorias aceitam `active=true/false`. Ative lojas/programas manualmente antes de importar ofertas que deles dependem.

### Cabeçalhos completos

Colunas opcionais podem ser omitidas; colunas obrigatórias não. Defaults: status draft, validation_status pending, active false, position 0. Campos opcionais vazios permanecem vazios. Proveniência, evidências, credenciais e metadados de revisão não são aceitos.

- **category:** name,slug,parent_id,description,position,active — obrigatório name.
- **merchant:** name,slug,website_url,allowed_domains,logo_url,description,status — obrigatório name.
- **program:** merchant_id,code,name,network,terms_url,tracking_domains,status — obrigatórios merchant_id,code.
- **product:** title,short_description,description,brand,model,gtin,category_id,image_url,attributes,status — obrigatório title; SKU gerado automaticamente.
- **variant:** product_id,variant_key,title,sku,gtin,attributes,image_url,status — obrigatórios product_id,variant_key.
- **offer:** product_id,merchant_id,variant_id,program_id,external_id,status — obrigatórios product_id,merchant_id.
- **link:** offer_id,destination_url,affiliate_url,tracking_code,expires_at,validation_status — obrigatórios offer_id,destination_url,affiliate_url.

### Tipos e validações

Texto simples, sem HTML/controles, com os limites de tamanho dos campos da curadoria. IDs: inteiros positivos até 2147483647; position: inteiro não negativo. active: exatamente true ou false. attributes: objeto JSON válido, sem NaN. GTIN: 8/12/13/14 dígitos, verificador válido; normalizado para 14. Slugs/chaves normalizados. Domínios: até 30 nomes completos separados por espaço, vírgula ou quebra de linha, sem protocolo, porta ou curingas. URLs: HTTPS sem credenciais, IP literal, porta alternativa, fragmento ou controles; imagens podem usar caminho local permanente seguro, não upload temporário. expires_at: ISO 8601 com fuso. Variante precisa pertencer ao produto da oferta e programa à loja. Links precisam usar domínios autorizados dessa loja/programa. Chaves únicas existentes ou repetidas no lote são rejeitadas.

Não importe preços, estoque, observações, fonte/horário de preço, revisão, evidência de venda ou status publicado/verificado. Os validadores existentes são reutilizados; nenhum valor importado vira observação de preço ou link válido. Pedidos históricos e demonstrações não são alterados. O cadastro de dados fornecidos não comprova sua origem ou veracidade; revisão permanece necessária.

## Relatórios

Ofertas com cliques são agregadas por `ProductLinkClick.offer_id` com vínculos reais a oferta, produto e loja. Paginação de 15 ofertas; resumo de até 15 lojas com mais cliques; filtre por ID para consultar uma loja específica. Datas inclusivas em UTC. Nome e título são os atuais, não os snapshots no momento do clique. Cliques sem offer_id permanecem separados como legado; o filtro de loja atual não os reatribui. Cliques não medem visitantes únicos, vendas, atribuição, conversões ou comissões.

## Checagem HTTP

Somente o ID da oferta é recebido; URLs e domínios vêm de registros persistidos. Ambos os URLs são checados. HTTPS e domínio permitido são validados antes de DNS. Todos os endereços resolvidos devem ser públicos; endereços privados, reservados, loopback, link-local, multicast e IPv4 mapeado são recusados. A conexão usa um IP aprovado fixado, Host/SNI do domínio original e verificação TLS; proxies de ambiente não são usados. Isso evita uma segunda resolução DNS durante a conexão.

Timeout total de 15 segundos por URL, conexão até 4 segundos e operações até 5 segundos. Redirects nunca são seguidos: 3xx requer revisão e é uma falha operacional conservadora. HEAD é tentado primeiro; apenas 405/501 permitem GET com Range e limite de 64 KiB de corpo bruto. Conteúdo não é salvo nem interpretado. Falhas DNS/TLS/HTTP/limite são visíveis, não simuladas. Alguns sites bloqueiam HEAD ou checagens automatizadas; uma falha pode ser bloqueio do servidor, não prova de remoção do produto.

Resultados registram horário, método, HTTP, URL efetivamente acessada, erro e saúde de rede, com auditoria na mesma transação. Se link/domínios mudarem durante a chamada, o resultado é descartado. Falhas invalidam o link e reavaliam publicações dependentes atomicamente; elegibilidade pública também recusa metadata de saúde falha. Sucesso não torna link pendente/inválido em válido. Após sucesso, reabra e revise manualmente antes de publicar. A revisão manual não apaga a falha anterior: é necessária uma checagem saudável. HEAD 200 não comprova correspondência do produto, preço, estoque, compra ou comissão.

## SEO e dependências reais

Títulos e descrições públicos refletem descoberta independente. Canonicals são caminhos internos fixos ou IDs de produto normalizados, sem parâmetros de busca. Páginas privadas e carrinho retirado recebem noindex. O sitemap operacional inclui apenas rotas públicas e produtos elegíveis, até 50.000 IDs; responde indisponível em vez de inventar um domínio canônico ou dados se a origem pública não estiver disponível. Não contém admin, conta, login ou carrinho. O sitemap é anunciado no head público; robots do serviço bloqueia superfícies privadas/legadas. Nenhum host enviado pelo visitante é usado como origem canônica. Não é gerado schema de venda/estoque fictício.

Conversões, comissões e atribuição aguardam APIs/relatórios oficiais de marketplaces/redes e permissão adequada; não podem ser inferidas de cliques. Notificações aguardam provedor real e consentimento. Agendamento recorrente, notificações e automações aguardam serviço de processamento de tarefas. Operação contínua, disponibilização dos endpoints públicos e retenção de dados exigem suporte dos serviços externos apropriados. Nenhuma dessas conexões foi inicializada ou simulada. Não coloque credenciais no CSV, em notas editoriais ou no painel. As checagens HTTP gerais usam httpx e não precisam de chaves de marketplace.
