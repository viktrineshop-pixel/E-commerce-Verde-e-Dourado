import reflex as rx
from app.states.account_state import AccountState, CustomerOrder, PurchasedItem
from app.states.favorite_state import FavoriteState
from app.components.favorites import favorites_section
from app.components.saved_lists import lists_section


def catalog_link() -> rx.Component:
    return rx.el.a(
        "Explorar ofertas",
        rx.icon("arrow-up-right", class_name="h-4 w-4"),
        href="/#catalogo",
        class_name="inline-flex w-fit items-center gap-4 border border-[#d4af37] bg-[#0d231d] px-6 py-3 text-xs font-medium text-[#f5f1e8] transition-colors hover:bg-[#17392e] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
    )


def account_intro() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "UM ESPAÇO SÓ SEU",
                    class_name="text-[10px] tracking-[0.22em] text-[#d4af37]",
                ),
                rx.el.h1(
                    "Minha conta",
                    class_name="mt-4 break-words font-['Cormorant_Garamond'] text-4xl font-medium leading-tight text-[#f5f1e8] sm:text-5xl lg:text-6xl",
                ),
                rx.el.p(
                    "Seus favoritos, listas privadas e arquivo demonstrativo na Viktrine. Compras acontecem nas lojas externas.",
                    class_name="mt-4 text-sm leading-7 text-[#c5c9bd]",
                ),
                rx.el.div(
                    rx.icon(
                        "user-round",
                        class_name="h-4 w-4 shrink-0 text-[#d4af37]",
                    ),
                    rx.el.span(
                        "Conta pessoal · acesso seguro",
                        class_name="text-xs text-[#c5c9bd]",
                    ),
                    class_name="mt-6 flex items-center gap-3",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("log-out", class_name="h-4 w-4"),
                "Sair da conta",
                on_click=FavoriteState.clear_presentation,
                type="button",
                class_name="flex w-fit items-center gap-3 border border-[#d4af37]/50 bg-transparent px-5 py-3 text-xs text-[#f5f1e8] hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
            ),
            class_name="mx-auto flex w-full max-w-[1440px] flex-col justify-between gap-8 px-6 py-12 sm:flex-row sm:items-center lg:px-12 lg:py-16",
        ),
        class_name="w-full border-t border-white/10 bg-[#05120e] text-[#f5f1e8]",
    )


def purchased_item(item: PurchasedItem) -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src=item["image_url"],
            alt=item["title"],
            loading="lazy",
            class_name="h-28 w-20 shrink-0 bg-[#efede4] object-cover sm:h-32 sm:w-24",
        ),
        rx.el.div(
            rx.el.p(
                item["category"],
                class_name="text-[9px] uppercase tracking-widest text-[#8b7846]",
            ),
            rx.el.h4(
                item["title"],
                class_name="mt-1 font-['Cormorant_Garamond'] text-2xl font-medium text-[#0d231d]",
            ),
            rx.el.p(
                item["description"],
                class_name="mt-2 text-xs leading-6 text-[#687268]",
            ),
            rx.el.p(
                f"Referência: {item['sku']}",
                class_name="mt-2 text-[10px] text-[#687268]",
            ),
            rx.el.div(
                rx.el.span(f"Quantidade: {item['quantity']}"),
                rx.el.span(f"Valor unitário: {item['unit_price']}"),
                rx.el.span(f"Desconto: {item['discount']}"),
                class_name="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-[#687268]",
            ),
            rx.el.p(
                f"Total da peça: {item['total']}",
                class_name="mt-3 text-sm font-medium text-[#0d231d]",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=item["id"],
        class_name="flex gap-4 border-b border-[#dedfd5] py-6 last:border-b-0 sm:gap-6",
    )


def amount_row(label: str, value: str) -> rx.Component:
    return rx.el.div(
        rx.el.dt(label),
        rx.el.dd(value),
        class_name="flex justify-between gap-6 py-2 text-xs text-[#687268]",
    )


def order_card(order: CustomerOrder) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rx.icon("package", class_name="h-5 w-5 text-[#8b7846]"),
                    class_name="hidden border border-[#d4af37]/25 bg-[#faf9f4] p-3 sm:block",
                ),
                rx.el.div(
                    rx.el.h3(
                        order["number"],
                        class_name="text-sm font-semibold tracking-wide text-[#0d231d]",
                    ),
                ),
                class_name="flex items-center gap-4",
            ),
            rx.el.div(
                rx.el.span(
                    order["status_label"],
                    class_name=rx.cond(
                        (order["status"] == "cancelled")
                        | (order["status"] == "refunded"),
                        "w-fit rounded-full bg-gray-100 px-3 py-1.5 text-[10px] font-medium text-gray-600",
                        "w-fit rounded-full bg-[#edf1e9] px-3 py-1.5 text-[10px] font-medium text-[#375340]",
                    ),
                ),
                rx.el.p(
                    order["total"],
                    class_name="text-lg font-medium text-[#0d231d]",
                ),
                class_name="flex flex-wrap items-center gap-5 sm:gap-8",
            ),
            class_name="flex flex-col justify-between gap-5 p-6 sm:flex-row sm:items-center lg:px-8",
        ),
        rx.el.details(
            rx.el.summary(
                rx.el.span("Consultar itens e dados históricos"),
                rx.icon(
                    "chevron-down",
                    class_name="h-4 w-4 transition-transform group-open:rotate-180",
                ),
                class_name="flex cursor-pointer list-none items-center justify-between gap-4 border-t border-[#dedfd5] bg-[#faf9f4] px-6 py-4 text-xs font-medium text-[#0d231d] hover:text-[#8b7846] focus-visible:outline-2 focus-visible:outline-[#d4af37] lg:px-8 [&::-webkit-details-marker]:hidden",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h4(
                        "Itens do arquivo",
                        class_name="font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
                    ),
                    rx.el.p(
                        "Peças e valores registrados no momento do pedido.",
                        class_name="mt-2 text-xs text-[#687268]",
                    ),
                    rx.cond(
                        order["items"].length() > 0,
                        rx.el.div(rx.foreach(order["items"], purchased_item)),
                        rx.el.p(
                            "Nenhuma peça registrada neste pedido.",
                            class_name="py-6 text-sm text-[#687268]",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h4(
                            rx.icon(
                                "map-pin", class_name="h-4 w-4 text-[#8b7846]"
                            ),
                            "Endereço registrado no arquivo",
                            class_name="flex items-center gap-2 text-sm font-semibold text-[#0d231d]",
                        ),
                        rx.el.p(
                            order["recipient"],
                            class_name="mt-5 text-sm font-medium text-[#0d231d]",
                        ),
                        rx.el.p(order["street"]),
                        rx.cond(
                            order["complement"] != "",
                            rx.el.p(order["complement"]),
                        ),
                        rx.el.p(order["neighborhood"]),
                        rx.el.p(order["city"]),
                        rx.el.p(
                            f"CEP {order['postal_code']} · {order['country']}"
                        ),
                        rx.el.p(
                            order["phone"],
                            class_name="mt-3 text-xs text-[#687268]",
                        ),
                        rx.el.p(
                            order["email"],
                            class_name="break-all text-xs text-[#687268]",
                        ),
                        class_name="border border-[#dedfd5] bg-[#faf9f4] p-5 text-xs leading-6 text-[#687268]",
                    ),
                    rx.el.dl(
                        amount_row("Subtotal", order["subtotal"]),
                        amount_row("Frete histórico", order["shipping"]),
                        amount_row("Desconto", order["discount"]),
                        rx.el.div(
                            rx.el.dt("Total do pedido"),
                            rx.el.dd(order["total"]),
                            class_name="mt-2 flex justify-between gap-4 border-t border-[#dedfd5] pt-4 text-sm font-semibold text-[#0d231d]",
                        ),
                        class_name="mt-5 border border-[#dedfd5] bg-[#faf9f4] p-5",
                    ),
                    class_name="min-w-0",
                ),
                class_name="grid gap-8 border-t border-[#dedfd5] p-6 lg:grid-cols-[minmax(0,1fr)_300px] lg:p-8",
            ),
            class_name="group",
        ),
        key=order["id"],
        class_name="w-full overflow-hidden border border-[#dedfd5] bg-white text-[#0d231d]",
    )


def orders_loading() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Carregando seus pedidos…", class_name="mb-4 text-sm text-[#687268]"
        ),
        rx.foreach(
            [1, 2, 3],
            lambda index: rx.el.div(
                key=index,
                class_name="mb-4 h-32 w-full animate-pulse border border-[#dedfd5] bg-[#efede4]",
            ),
        ),
        role="status",
        aria_live="polite",
        aria_busy=True,
    )


def orders_error() -> rx.Component:
    return rx.el.div(
        rx.icon("circle-alert", class_name="mx-auto h-7 w-7 text-[#8b7846]"),
        rx.el.h3(
            "Vamos tentar de novo?",
            class_name="mt-4 font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
        ),
        rx.el.p(
            AccountState.error,
            class_name="mt-3 text-sm leading-7 text-[#687268]",
        ),
        rx.el.button(
            "Tentar novamente",
            rx.icon("refresh-cw", class_name="h-4 w-4"),
            on_click=AccountState.refresh_orders,
            class_name="mx-auto mt-6 flex items-center gap-3 border border-[#0d231d] bg-[#0d231d] px-6 py-3 text-xs text-[#f5f1e8] hover:bg-[#17392e] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        rx.el.a(
            "Voltar ao catálogo",
            href="/#catalogo",
            class_name="mt-5 inline-block text-xs text-[#687268] underline underline-offset-4 hover:text-[#0d231d]",
        ),
        role="alert",
        class_name="border border-[#dedfd5] bg-white px-6 py-14 text-center",
    )


def orders_empty() -> rx.Component:
    return rx.el.div(
        rx.icon("shopping-bag", class_name="mx-auto h-9 w-9 text-[#a68c3a]"),
        rx.el.h3(
            "Nenhum registro histórico nesta conta.",
            class_name="mt-6 font-['Cormorant_Garamond'] text-3xl text-[#0d231d] sm:text-4xl",
        ),
        rx.el.p(
            "Não há pedidos anteriores associados à sua identidade neste arquivo demonstrativo.",
            class_name="mx-auto mt-4 max-w-lg text-sm leading-7 text-[#687268]",
        ),
        rx.el.p(
            "A Viktrine não cria novos pedidos. Compras externas não aparecem neste arquivo; favoritos e listas não são reservas.",
            class_name="mx-auto mt-3 max-w-lg text-xs leading-6 text-[#687268]",
        ),
        rx.el.div(catalog_link(), class_name="mt-8 flex justify-center"),
        class_name="border border-[#dedfd5] bg-white px-6 py-16 text-center",
    )


def account_content() -> rx.Component:
    return rx.fragment(
        account_intro(),
        rx.el.section(
            rx.el.a(
                rx.icon("arrow-left", class_name="h-3.5 w-3.5"),
                "Voltar ao catálogo",
                href="/#catalogo",
                class_name="mb-10 inline-flex items-center gap-2 text-xs text-[#687268] hover:text-[#0d231d]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        "MINHA CONTA",
                        class_name="text-[10px] tracking-[0.2em] text-[#8b7846]",
                    ),
                    rx.el.h2(
                        "Arquivo demonstrativo de pedidos anteriores",
                        class_name="mt-2 font-['Cormorant_Garamond'] text-4xl text-[#0d231d] sm:text-5xl",
                    ),
                    rx.el.p(
                        "Somente leitura. Valores, endereços e status são registros antigos, não confirmação de venda, pagamento ou entrega.",
                        class_name="mt-3 text-sm text-[#687268]",
                    ),
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-4 w-4"),
                    "Atualizar arquivo",
                    on_click=AccountState.refresh_orders,
                    disabled=AccountState.loading,
                    class_name="flex w-fit items-center gap-2 border border-[#dedfd5] bg-white px-4 py-3 text-xs text-[#0d231d] hover:border-[#d4af37] disabled:cursor-wait disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                class_name="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end",
            ),
            rx.cond(
                AccountState.loading,
                orders_loading(),
                rx.cond(
                    AccountState.error != "",
                    orders_error(),
                    rx.cond(
                        AccountState.orders.length() == 0,
                        orders_empty(),
                        rx.el.div(
                            rx.el.div(
                                rx.foreach(AccountState.orders, order_card),
                                class_name="flex w-full flex-col gap-5",
                            ),
                            rx.el.nav(
                                rx.el.button(
                                    rx.icon(
                                        "chevron-left", class_name="h-4 w-4"
                                    ),
                                    "Anteriores",
                                    on_click=AccountState.previous_page,
                                    disabled=AccountState.page_number == 1,
                                    class_name="flex items-center gap-2 border border-[#dedfd5] bg-white px-4 py-3 text-xs text-[#0d231d] hover:border-[#d4af37] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                                ),
                                rx.el.span(
                                    f"Página {AccountState.page_number}",
                                    class_name="text-xs text-[#687268]",
                                ),
                                rx.el.button(
                                    "Próximos",
                                    rx.icon(
                                        "chevron-right", class_name="h-4 w-4"
                                    ),
                                    on_click=AccountState.next_page,
                                    disabled=~AccountState.has_next,
                                    class_name="flex items-center gap-2 border border-[#dedfd5] bg-white px-4 py-3 text-xs text-[#0d231d] hover:border-[#d4af37] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                                ),
                                aria_label="Paginação dos pedidos",
                                class_name="mt-8 flex flex-wrap items-center justify-between gap-4",
                            ),
                            rx.el.p(
                                "Status preservados apenas como dados históricos. A Viktrine não processa novos pedidos, pagamentos ou envios.",
                                class_name="mt-6 text-xs leading-6 text-[#687268]",
                            ),
                        ),
                    ),
                ),
            ),
            class_name="mx-auto w-full max-w-[1440px] px-6 py-10 text-[#0d231d] lg:px-12 lg:py-14",
        ),
        favorites_section(),
        lists_section(),
    )
