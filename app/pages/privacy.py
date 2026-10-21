import reflex as rx
from app.components.header import header
from app.components.hero import footer


def privacy_section(title: str, body: str) -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            title,
            class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
        ),
        rx.el.p(body, class_name="mt-4 text-sm leading-7 text-[#536059]"),
        class_name="min-w-0 border-t border-[#d4af37]/35 py-7",
    )


def privacy_content() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            rx.el.a(
                "Voltar à descoberta",
                href="/",
                class_name="inline-flex min-h-11 items-center text-sm text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.p(
                "Viktrine · TRANSPARÊNCIA",
                class_name="mt-8 text-xs tracking-[0.2em] text-[#71602f]",
            ),
            rx.el.h1(
                "Privacidade e LGPD",
                class_name="mt-4 font-['Cormorant_Garamond'] text-5xl text-[#073238] md:text-6xl",
            ),
            rx.el.p(
                "Como os recursos atuais utilizam dados — e o que ainda está pendente. Este aviso descreve práticas implementadas; não é uma certificação de conformidade legal.",
                class_name="mt-6 mb-10 text-sm leading-7 text-[#536059]",
            ),
            rx.el.div(
                privacy_section(
                    "Identidade e acesso",
                    "A descoberta pública não exige login. Ao entrar, a identidade autenticada fornece um identificador de conta e, quando disponíveis, nome, e-mail e imagem. O identificador associa favoritos, listas privadas e pedidos históricos à sua conta. Nome e e-mail também podem ser registrados para identificação e controle de acesso administrativo. A sessão de autenticação é usada para manter o acesso; não há login ou compra de produtos próprios da Viktrine.",
                ),
                privacy_section(
                    "Favoritos, listas e notas",
                    "Produtos favoritos, nomes e descrições das listas e notas adicionadas são persistidos e associados à identidade da conta. Você pode remover favoritos e excluir listas e seus itens na Minha conta. Essas ações removem as respectivas referências salvas, não apagam a identidade autenticada ou o arquivo de pedidos. Evite incluir dados sensíveis em notas. Salvar produtos não registra compras ou reservas.",
                ),
                privacy_section(
                    "Cliques e encaminhamentos",
                    "Ao seguir um link elegível, a Viktrine registra o identificador da oferta e a data e hora do clique, além de referências do produto e da loja, para relatórios de encaminhamento. Esse registro de clique não contém um campo de identidade do visitante, IP ou navegador. Cliques não comprovam pessoas únicas, vendas ou conversões. Logs técnicos dos serviços que atendem a navegação podem existir; este aviso não promete anonimato completo ou ausência de logs de infraestrutura.",
                ),
                privacy_section(
                    "Arquivo demonstrativo anterior",
                    "Pedidos e itens existentes permanecem preservados, incluindo valores, contato, endereço e status registrados na antiga demonstração. Na Minha conta, somente pedidos associados ao seu identificador autenticado são consultados; a administração autorizada consulta o arquivo histórico. É somente leitura, sem criação de novos pedidos ou alterações de pagamento, envio e status. Registros não comprovam compras reais e compras em lojas externas não são importadas.",
                ),
                privacy_section(
                    "Lojas externas e afiliados",
                    "Links podem encaminhar a programas de afiliados e a Viktrine pode receber comissão por compras externas. O destino aplica suas próprias políticas de privacidade, cookies, pagamento e entrega. Imagens de produtos, fontes tipográficas e outros recursos externos são carregados de seus respectivos provedores, que recebem as requisições do navegador. Uma página editorial de loja não indica endosso ou integração oficial.",
                ),
                privacy_section(
                    "Observações, não integrações ao vivo",
                    "Preços e fontes são observações inseridas pela administração e revisadas editorialmente. Histórico de preços só aparece quando existem observações registradas. Não há integração ao vivo com varejistas, confirmação de conversões, notificações conectadas ou checkout de produtos. Cupons informativos e condições devem ser confirmados no destino.",
                ),
                privacy_section(
                    "Acesso, correção e exclusão",
                    "Você pode consultar seus favoritos, listas e arquivo na Minha conta e gerenciar os dados salvos pelos controles existentes. O canal oficial para solicitações de acesso, correção ou exclusão de dados pessoais está pendente de definição; não há e-mail, telefone ou formulário confirmado para esse atendimento. Não apresentamos links sociais pendentes como canal de privacidade. A exclusão integral da conta e do arquivo não está disponível por um controle nesta aplicação.",
                ),
                privacy_section(
                    "Retenção e limites deste aviso",
                    "Dados salvos e registros históricos permanecem armazenados enquanto não forem removidos pelos controles disponíveis ou por um procedimento administrativo aplicável. Não há prazo de retenção automático ou fluxo completo de atendimento LGPD confirmado nesta interface. A identificação do responsável, o canal de atendimento, os prazos e as bases legais devem ser formalizados antes de anunciar atendimento integral ou conformidade. Este aviso não inventa garantias, contatos ou integrações.",
                ),
                class_name="grid w-full grid-cols-1 gap-x-12 md:grid-cols-2",
            ),
            class_name="mx-auto w-full max-w-[1440px] px-6 py-12 lg:px-12 lg:py-16",
        ),
        footer(),
        class_name="min-h-dvh w-full bg-[#faf9f4] font-['Inter'] text-[#073238]",
    )
