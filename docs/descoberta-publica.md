# Descoberta pública da Viktrine

A descoberta lê produtos editoriais publicados e ofertas publicadas com loja ativa, categoria e ancestrais ativos, variante publicada quando especificada, programa ativo quando associado, observação persistida correspondente ao preço/fonte/moeda/horário e link validado manualmente, não expirado e em domínio autorizado. Produtos DEMO-* não são públicos. Não há scraping ou chamadas a APIs de marketplaces.

Busca usa palavras de título, marca e modelo com parâmetros SQL. Categorias incluem descendentes; a faixa monetária é em BRL. Ordenação de preço separa moedas. Paginação é por grupo de produto, variante e moeda; cada grupo mostra suas ofertas elegíveis. Comparações não somam frete, não aplicam cupons e não prometem disponibilidade ou atualização automática.

A página de produto apresenta horários editoriais, da oferta, da observação e da revisão manual do link. Histórico exige duas observações persistidas da mesma oferta e moeda; são exibidas as 100 mais recentes em ordem cronológica. Campanhas aparecem somente por associação explícita à oferta e dentro de suas datas publicadas. Datas ausentes são identificadas como não informadas.

O modelo Coupon atual contém somente cupons locais legados, sem vínculo a Merchant e sem termos externos verificáveis. Esses códigos não são exibidos como cupons de marketplace e não são descontados das ofertas. A ausência de vínculo não é preenchida por inferência do nome, código ou loja histórica do produto.

Favoritos usam List/ListItem com uma lista privada reservada. Favoritos legados da mesma identidade são transferidos de forma idempotente, preservando os horários e removendo a origem somente após a inserção na mesma transação. Listas nomeadas são privadas, paginadas e verificadas pelo sub autenticado no servidor. Produtos fora da descoberta podem ser removidos de listas, mas não adicionados. Os nomes, descrições e notas aceitos são salvos exatamente como enviados. Logout limpa a apresentação e invalida respostas pendentes.

Encaminhamento por oferta resolve somente URLs persistidas e elegíveis. IDs inválidos, publicação retirada, link expirado/fora do domínio e falhas de gravação não produzem encaminhamento afiliado nem registro de clique. A rota histórica de produto resolve uma oferta atual elegível, nunca o URL legado. Cliques são registros de encaminhamento; não significam venda ou conversão.

Os testes em scripts/test_public_catalog.py cobrem contrato de publicação, URLs e IDs inválidos. Não executam login nem alteram tabelas. A verificação de banco opcional somente consulta dados existentes.
