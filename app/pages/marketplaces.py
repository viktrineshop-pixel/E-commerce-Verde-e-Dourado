import reflex as rx
import reflex_enterprise as rxe
from app.components.marketplace import marketplace_content


@rx.page(
    route="/lojas/amazon",
    title="Amazon · Curadoria independente | Viktrine",
    description="Orientações editoriais independentes da Viktrine. Sem endosso, catálogo oficial ou integração com a Amazon.",
)
def amazon_page() -> rx.Component:
    return marketplace_content(
        name="Amazon",
        headline="Essenciais que acompanham a sua rotina.",
        intro="Neste espaço independente dedicado ao tema Amazon, apresentamos sugestões editoriais para orientar escolhas. Os atalhos levam à descoberta geral da Viktrine, não a uma seleção de produtos da Amazon.",
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
        guide_body="Use estas orientações na descoberta geral, sem confundi-las com anúncios da Amazon. Não há seleção específica desta loja nesta página.",
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
                "body": "Consulte os detalhes do produto, a data e a fonte da oferta. “Ir para a loja” só está disponível para ofertas elegíveis com links revisados; confirme as condições no destino.",
            },
        ],
    )


@rxe.page(
    route="/lojas/shopee",
    auth=False,
    title="Shopee · Curadoria independente | Viktrine",
    description="Orientações de descoberta e comparação da Viktrine. Sem endosso, catálogo oficial ou integração com a Shopee.",
)
def shopee_page() -> rx.Component:
    return marketplace_content(
        name="Shopee",
        headline="Novas ideias para o seu jeito de vestir.",
        intro="A página temática Shopee é o nosso convite para experimentar: variar um acessório, descobrir uma textura ou olhar de novo para uma combinação. As orientações são independentes, sem produtos específicos da Shopee nesta página.",
        categories=[
            {
                "number": "01",
                "category": "Descoberta",
                "title": "Um novo ponto de partida",
                "body": "Explore somente produtos com ofertas elegíveis na descoberta geral. Use as categorias reais disponíveis nos filtros.",
            },
            {
                "number": "02",
                "category": "Acessórios",
                "title": "Mude só um detalhe",
                "body": "Experimente o contraste de uma bolsa caramelo, a presença de um relógio dourado ou a linha de uma armação clássica. Pequenas escolhas renovam os básicos.",
            },
            {
                "number": "03",
                "category": "Comparação",
                "title": "Olhe além do desconto",
                "body": "Compare a mesma variante e moeda. Consulte datas e fontes; esta página não promete promoções da Shopee.",
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
                "body": "Na descoberta geral, use os filtros reais de preço, categoria e loja. Preços são observações inseridas pela administração, não consultas ao vivo à Shopee.",
            },
        ],
    )


@rxe.page(
    route="/lojas/mercado-livre",
    auth=False,
    title="Mercado Livre · Curadoria independente | Viktrine",
    description="Orientações editoriais da Viktrine. Sem endosso, catálogo oficial ou integração com o Mercado Livre.",
)
def mercado_livre_page() -> rx.Component:
    return marketplace_content(
        name="Mercado Livre",
        headline="Escolhas práticas. Estilo todos os dias.",
        intro="Na nossa página temática Mercado Livre, o olhar editorial vai para a praticidade: vestir com conforto, organizar os essenciais e montar combinações para uma rotina real. Os atalhos levam à descoberta geral da Viktrine, não a um catálogo do Mercado Livre.",
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
                "body": "Tricô, denim e vestidos leves sugerem combinações para diferentes momentos. Consulte fontes e datas das ofertas na descoberta geral e confirme disponibilidade no destino.",
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
                "body": "Consulte a descrição e a data da observação. A Viktrine não tem estoque próprio; disponibilidade e condições devem ser confirmadas na loja externa.",
            },
            {
                "title": "Entenda o destino de cada produto",
                "body": "“Ir para a loja” encaminha por um link de oferta elegível e revisado. A Viktrine pode receber comissão, mas não processa compras, pagamentos ou entregas nem confirma conversões.",
            },
        ],
    )
