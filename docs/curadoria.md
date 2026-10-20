# Curadoria editorial da Viktrine

O espaço de curadoria fica em `/admin`, com o acesso administrativo e o primeiro administrador existentes. Nesta etapa, pedidos históricos, relatórios e cupons permanecem disponíveis abaixo da curadoria.

## Fluxo de cadastro

1. Cadastre uma categoria ativa (e ancestrais ativos). Cadastre a loja, seu site HTTPS e seus domínios oficiais. Se houver programa de afiliados, registre-o para essa loja e informe os domínios de tracking autorizados. O cadastro do programa não conecta uma API.
2. Crie um produto editorial como rascunho. Marca, modelo, GTIN, categoria, atributos e proveniência podem ser informados gradualmente. GTIN tem dígito verificador validado e é normalizado para 14 dígitos. Slugs são normalizados. O SKU editorial é estável.
3. Cadastre variantes, quando necessárias, com chave, título e atributos. Os IDs na lista identificam os vínculos; o filtro de produto permite trabalhar registros relacionados. Não altere o proprietário de um registro existente: crie outro registro para outro produto ou loja.
4. Salve a oferta como rascunho, vinculada a produto, loja ativa e, opcionalmente, variante e programa compatíveis. Cada oferta tem seu próprio editor e um único link. Uma mudança no link não altera links de outras ofertas.
5. Registre uma observação de preço real com preço em BRL, fonte, horário com fuso e URL de evidência no domínio da loja. Confirme que essa observação efetivamente ocorreu. O preço legado demonstrativo nunca é copiado para observações ou ofertas. Observações são imutáveis; registre uma nova observação para corrigir ou atualizar. Uma observação mais antiga é histórica e não substitui o preço corrente.
6. Cadastre o link da oferta: destino HTTPS em domínio oficial da loja e URL HTTPS de afiliado no domínio da loja ou tracking do programa dessa mesma loja. Revise manualmente a correspondência ao mesmo item/oferta e a expiração, marque a confirmação e salve como válido. Essa revisão não é teste de redirecionamento nem comprovação de saúde do link.
7. Reabra a oferta, confirme a revisão e publique. A publicação exige observação correspondente ao preço/fonte/horário, evidência, variante publicada quando aplicável, categoria ativa, loja/programa compatíveis e link válido revisado e não expirado.
8. Revise os candidatos a duplicados. São candidatos por GTIN de produtos/variantes ou marca+modelo normalizados para comparação. Registre uma decisão com justificativa. Não há mesclagem nem exclusão automática. Pendências e decisões de duplicado impedem publicação editorial.
9. Reabra o produto, forneça título, resumo, descrição e imagem permanente segura, confirme a revisão e publique. É necessária ao menos uma oferta publicada válida desse produto. Produtos com SKU demonstrativo permanecem rascunhos.
10. Salve a campanha como rascunho, associe ofertas pelo painel de associações e depois publique. Campanhas publicadas exigem ofertas publicadas válidas e datas coerentes.

## Evidência e responsabilidade

A curadoria é manual. Não foram implementadas consulta automática de marketplace, verificação HTTP/redirecionamento, atribuição de venda ou comissão. O registro de uma URL ou de um programa não comprova integração externa. Observações mostram apenas preços efetivamente fornecidos pelo administrador e não prometem disponibilidade atual.

Cada salvamento exige um motivo e ocorre na mesma transação que a auditoria. O histórico somente leitura apresenta sujeito responsável, entidade, ID, motivo e campos antes/depois. Alterações inválidas ou conflitos não são confirmados. Edições concorrentes exigem reabrir o registro. Vínculos principais de ofertas, variantes, programas, links e associações são imutáveis.

Editar produto/oferta exige reconfirmar a revisão; uma nova observação corrente põe a oferta em rascunho. Alterar categoria, loja, programa, variante ou link revalida as publicações dependentes. Publicações que deixam de atender aos critérios são retiradas para rascunho e auditadas na mesma transação. Não há exclusão física de registros editoriais; use arquivamento ou inativação quando o tipo de registro permitir.

## Testes

O arquivo `scripts/test_discovery.py` cobre normalização de slug/GTIN, URLs HTTPS e correspondência de domínio, datas com fuso, objetos JSON, ausência de preço/estoque no cadastro editorial e snapshots de auditoria. Os testes não fazem consultas de marketplace e não geram evidências fictícias.
