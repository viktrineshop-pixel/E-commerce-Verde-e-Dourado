import reflex as rx
import reflex_enterprise as rxe
from app.components.marketplace import marketplace_content


@rx.page(
    route="/lojas/amazon",
    title="Amazon · Curadoria independente | VIKTRINE SHOP",
    description="Essenciais e combinações atemporais no catálogo demonstrativo da VIKTRINE SHOP. Sem vínculo ou integração com a Amazon.",
)
def amazon_page() -> rx.Component:
    return marketplace_content(
        name="Amazon",
        headline="Essenciais que acompanham a sua rotina.",
        intro="Neste espaço dedicado ao tema Amazon, nossa proposta editorial é começar pelo que permanece: peças versáteis, combinações simples e detalhes bem escolhidos. Explore a nossa própria vitrine, sem sair da VIKTRINE SHOP.",
        categories=[
            {
                "number": "01",
                "category": "Masculino",
                "title": "A base de um bom look",
                "body": "Camisas clássicas e propostas casuais para alternar entre compromissos e momentos de descanso. Comece por uma base neutra e acrescente personalidade nos detalhes.",
            },
            {
                "number": "02",
                "category": "Feminino",
                "title": "Leveza para repetir",
                "body": "Linho, texturas suaves e sobreposições dão novas possibilidades à rotina. Explore vestidos e peças que conversam com diferentes momentos do dia.",
            },
            {
                "number": "03",
                "category": "Acessórios",
                "title": "Detalhes duradouros",
                "body": "Uma bolsa em tom caramelo, um relógio clássico ou óculos de inspiração atemporal: descubra pequenos pontos de destaque para as suas combinações.",
            },
        ],
        guide_title="Menos peças. Mais combinações.",
        guide_body="Um guarda-roupa versátil começa por escolhas que funcionam juntas. Use estas sugestões para percorrer o catálogo demo com intenção, sem confundir nossa seleção com anúncios da Amazon.",
        tips=[
            {
                "title": "Comece por uma paleta simples",
                "body": "Branco, tons naturais e denim facilitam combinações. Escolha uma base e varie a textura ou o acessório.",
            },
            {
                "title": "Pense em três ocasiões",
                "body": "Antes de escolher uma peça, imagine como ela entra em um dia de trabalho, um passeio e um encontro casual.",
            },
            {
                "title": "Leia os detalhes da peça",
                "body": "Abra o nome da loja parceira nos cards para conhecer a descrição do produto. Use “Ir para a loja” para acessar o link HTTPS cadastrado ou, quando não houver um link válido, a página interna da loja.",
            },
        ],
    )


@rxe.page(
    route="/lojas/shopee",
    auth=False,
    title="Shopee · Curadoria independente | VIKTRINE SHOP",
    description="Inspiração para experimentar detalhes e descobrir novidades na vitrine demo. Sem vínculo ou integração com a Shopee.",
)
def shopee_page() -> rx.Component:
    return marketplace_content(
        name="Shopee",
        headline="Novas ideias para o seu jeito de vestir.",
        intro="A página temática Shopee é o nosso convite para experimentar: variar um acessório, descobrir uma textura ou olhar de novo para uma combinação. A seleção é editorial e usa exclusivamente o catálogo demonstrativo da VIKTRINE SHOP.",
        categories=[
            {
                "number": "01",
                "category": "Novidades",
                "title": "Um novo ponto de partida",
                "body": "Conheça as peças marcadas como novidade na vitrine demo. Um vestido leve ou um tricô de textura suave pode inspirar uma composição diferente.",
            },
            {
                "number": "02",
                "category": "Acessórios",
                "title": "Mude só um detalhe",
                "body": "Experimente o contraste de uma bolsa caramelo, a presença de um relógio dourado ou a linha de uma armação clássica. Pequenas escolhas renovam os básicos.",
            },
            {
                "number": "03",
                "category": "Promoções",
                "title": "Olhe além do desconto",
                "body": "Explore os produtos com preço comparativo no catálogo demonstrativo. Observe a proposta de uso antes do valor: não há cupons ou ofertas da Shopee nesta página.",
            },
        ],
        guide_title="Experimente sem perder a sua essência.",
        guide_body="Não é preciso mudar tudo para criar um look novo. Estas ideias ajudam a explorar os produtos da nossa vitrine com criatividade e sem promessas de ofertas externas.",
        tips=[
            {
                "title": "Escolha um protagonista",
                "body": "Deixe uma textura, uma cor ou um acessório conduzir a combinação. O restante pode ser simples e confortável.",
            },
            {
                "title": "Reinvente o que já combina",
                "body": "Imagine um mesmo básico com uma bolsa diferente ou uma sobreposição. Prefira escolhas que aproveitam o seu estilo atual.",
            },
            {
                "title": "Compare com calma",
                "body": "Use os filtros de preço e a ordenação no catálogo abaixo. Os preços comparativos são da demonstração; não representam promoções ou condições da Shopee.",
            },
        ],
    )


@rxe.page(
    route="/lojas/mercado-livre",
    auth=False,
    title="Mercado Livre · Curadoria independente | VIKTRINE SHOP",
    description="Escolhas práticas para o cotidiano no catálogo demo da VIKTRINE SHOP. Sem vínculo ou integração com o Mercado Livre.",
)
def mercado_livre_page() -> rx.Component:
    return marketplace_content(
        name="Mercado Livre",
        headline="Escolhas práticas. Estilo todos os dias.",
        intro="Na nossa página temática Mercado Livre, o olhar editorial vai para a praticidade: vestir com conforto, organizar os essenciais e montar combinações para uma rotina real. Todos os caminhos levam à vitrine demonstrativa interna da VIKTRINE SHOP.",
        categories=[
            {
                "number": "01",
                "category": "Masculino",
                "title": "Do compromisso ao passeio",
                "body": "Explore a proposta de uma camisa branca e de um tênis urbano para criar uma base casual. Escolha peças pensando nos trajetos e compromissos do seu dia.",
            },
            {
                "number": "02",
                "category": "Acessórios",
                "title": "Essenciais à mão",
                "body": "Uma bolsa para os pequenos objetos, um relógio como detalhe e óculos para completar a composição: conheça a proposta de cada acessório no catálogo.",
            },
            {
                "number": "03",
                "category": "Feminino",
                "title": "Camadas para a rotina",
                "body": "Tricô, denim e vestidos leves sugerem combinações para diferentes momentos. Confira os detalhes e a disponibilidade demonstrativa antes de usar “Ir para a loja”.",
            },
        ],
        guide_title="Escolha pela rotina que você tem.",
        guide_body="A melhor inspiração é aquela que faz sentido no cotidiano. Use este roteiro para conhecer a nossa seleção, sem atribuir a ela garantias, entregas ou condições do Mercado Livre.",
        tips=[
            {
                "title": "Defina o uso principal",
                "body": "Pense em conforto, frequência de uso e combinação com outras peças. Uma escolha prática tem lugar claro na sua rotina.",
            },
            {
                "title": "Confira a descrição e a disponibilidade",
                "body": "Abra os detalhes dos cards e use o filtro “Somente disponíveis”. A disponibilidade exibida pertence ao catálogo demo, não ao Mercado Livre.",
            },
            {
                "title": "Entenda o destino de cada produto",
                "body": "“Ir para a loja” abre o link HTTPS cadastrado para o produto. Sem um link válido, abre a página interna da loja parceira. A sacola e o checkout legado são separados desses links e continuam demonstrativos, sem cobrança nem entrega.",
            },
        ],
    )
