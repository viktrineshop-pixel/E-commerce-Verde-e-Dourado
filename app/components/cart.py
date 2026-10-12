import reflex as rx
from app.states.cart_state import CartState, CartLine


def cart_line(item: CartLine) -> rx.Component:
    return rx.el.article(
        rx.el.img(
            src=item["image_url"],
            alt=item["title"],
            class_name="h-32 w-24 shrink-0 bg-[#e9e6df] object-cover sm:h-40 sm:w-32",
        ),
        rx.el.div(
            rx.el.h2(
                item["title"],
                class_name="text-sm font-medium text-[#0d231d] sm:text-base",
            ),
            rx.el.p(
                f"{item['unit_price']} / unidade",
                class_name="mt-2 text-xs text-[#536059]",
            ),
            rx.cond(
                item["quantity"] > item["stock"],
                rx.el.p(
                    "Estoque insuficiente. Reduza a quantidade ou remova a peça.",
                    role="alert",
                    class_name="mt-2 text-xs text-red-600",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.button(
                        rx.icon("minus", class_name="h-4 w-4"),
                        type="button",
                        aria_label=f"Diminuir quantidade de {item['title']}",
                        disabled=(item["quantity"] <= 1)
                        | CartState.busy
                        | CartState.submitting,
                        on_click=CartState.change_quantity(
                            item["product_id"], -1
                        ),
                        class_name="flex h-10 w-10 items-center justify-center bg-transparent text-[#0d231d] hover:bg-[#edece3] focus-visible:outline-2 focus-visible:outline-[#8b7846] disabled:opacity-30",
                    ),
                    rx.el.span(
                        item["quantity"],
                        aria_label="Quantidade",
                        class_name="min-w-8 text-center text-sm text-[#0d231d]",
                    ),
                    rx.el.button(
                        rx.icon("plus", class_name="h-4 w-4"),
                        type="button",
                        aria_label=f"Aumentar quantidade de {item['title']}",
                        disabled=(item["quantity"] >= item["stock"])
                        | CartState.busy
                        | CartState.submitting,
                        on_click=CartState.change_quantity(
                            item["product_id"], 1
                        ),
                        class_name="flex h-10 w-10 items-center justify-center bg-transparent text-[#0d231d] hover:bg-[#edece3] focus-visible:outline-2 focus-visible:outline-[#8b7846] disabled:opacity-30",
                    ),
                    class_name="flex items-center border border-[#d8d7cc]",
                ),
                rx.el.button(
                    rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                    "Remover",
                    type="button",
                    aria_label=f"Remover {item['title']} da sacola",
                    on_click=CartState.remove_product(item["product_id"]),
                    disabled=CartState.busy | CartState.submitting,
                    class_name="flex min-h-10 items-center gap-2 bg-transparent px-2 text-xs text-[#536059] underline underline-offset-4 hover:text-[#0d231d] focus-visible:outline-2 focus-visible:outline-[#8b7846] disabled:opacity-40",
                ),
                class_name="mt-5 flex flex-wrap items-center gap-3",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.p(
            item["line_total"],
            class_name="w-full text-right text-sm font-semibold text-[#0d231d] sm:w-auto",
        ),
        key=item["product_id"],
        class_name="flex flex-wrap gap-4 border-b border-[#deded3] py-6 sm:flex-nowrap sm:gap-6",
    )


def checkout_field(
    name: str,
    label: str,
    placeholder: str,
    autocomplete: str,
    input_type: str = "text",
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=name,
            class_name="mb-2 block text-xs font-medium text-[#0d231d]",
        ),
        rx.el.input(
            name=name,
            id=name,
            type=input_type,
            placeholder=placeholder,
            auto_complete=autocomplete,
            default_value=CartState.draft.get(name, ""),
            aria_invalid=CartState.errors.get(name, "") != "",
            aria_describedby=f"{name}-error",
            max_length=320,
            disabled=CartState.submitting,
            class_name=rx.cond(
                CartState.errors.get(name, "") != "",
                "w-full rounded-sm border border-red-500 bg-white px-3 py-3 text-sm text-[#0d231d] placeholder:text-[#8b9289] focus:outline-2 focus:outline-red-500 disabled:opacity-60",
                "w-full rounded-sm border border-[#d8d7cc] bg-white px-3 py-3 text-sm text-[#0d231d] placeholder:text-[#8b9289] focus:border-[#8b7846] focus:outline-2 focus:outline-[#8b7846] disabled:opacity-60",
            ),
        ),
        rx.el.p(
            CartState.errors.get(name, ""),
            id=f"{name}-error",
            class_name="mt-1 min-h-4 text-xs text-red-600",
        ),
        class_name="min-w-0",
    )


def checkout_form() -> rx.Component:
    return rx.el.form(
        rx.el.h2(
            "Dados para atendimento e entrega",
            class_name="font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
        ),
        rx.el.p(
            "Todos os campos são obrigatórios, exceto complemento. Não é necessário criar uma conta.",
            class_name="mt-2 text-xs leading-relaxed text-[#536059]",
        ),
        rx.el.fieldset(
            rx.el.legend(
                "Contato",
                class_name="mb-4 text-sm font-semibold text-[#0d231d]",
            ),
            rx.el.div(
                checkout_field(
                    "recipient",
                    "Nome do destinatário",
                    "Nome completo",
                    "shipping name",
                ),
                checkout_field(
                    "phone", "Telefone com DDD", "(11) 99999-9999", "tel", "tel"
                ),
                checkout_field(
                    "email",
                    "E-mail de contato",
                    "voce@exemplo.com",
                    "email",
                    "email",
                ),
                class_name="grid grid-cols-1 gap-x-5 gap-y-3 sm:grid-cols-2",
            ),
            class_name="mt-7 min-w-0",
        ),
        rx.el.fieldset(
            rx.el.legend(
                "Endereço no Brasil",
                class_name="mb-4 text-sm font-semibold text-[#0d231d]",
            ),
            rx.el.div(
                checkout_field(
                    "cep", "CEP", "00000-000", "shipping postal-code"
                ),
                checkout_field(
                    "street",
                    "Rua / Avenida",
                    "Nome da rua",
                    "shipping address-line1",
                ),
                checkout_field("number", "Número", "123 ou S/N", "off"),
                checkout_field(
                    "complement",
                    "Complemento (opcional)",
                    "Apartamento, bloco…",
                    "shipping address-line2",
                ),
                checkout_field(
                    "neighborhood",
                    "Bairro",
                    "Seu bairro",
                    "shipping address-level3",
                ),
                checkout_field(
                    "city", "Cidade", "Sua cidade", "shipping address-level2"
                ),
                rx.el.div(
                    rx.el.label(
                        "Estado (UF)",
                        html_for="state",
                        class_name="mb-2 block text-xs font-medium text-[#0d231d]",
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.el.option("Selecione a UF", value=""),
                            rx.foreach(
                                "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(),
                                lambda uf: rx.el.option(uf, value=uf),
                            ),
                            id="state",
                            name="state",
                            default_value=CartState.draft.get("state", ""),
                            auto_complete="shipping address-level1",
                            disabled=CartState.submitting,
                            aria_invalid=CartState.errors.get("state", "")
                            != "",
                            aria_describedby="state-error",
                            class_name="w-full appearance-none rounded-sm border border-[#d8d7cc] bg-white px-3 py-3 pr-10 text-sm text-[#0d231d] focus:outline-2 focus:outline-[#8b7846] disabled:opacity-60",
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#536059]",
                        ),
                        class_name="relative",
                    ),
                    rx.el.p(
                        CartState.errors.get("state", ""),
                        id="state-error",
                        class_name="mt-1 min-h-4 text-xs text-red-600",
                    ),
                ),
                class_name="grid grid-cols-1 gap-x-5 gap-y-3 sm:grid-cols-2",
            ),
            class_name="mt-6 min-w-0",
        ),
        rx.el.div(
            rx.icon(
                "info", class_name="mt-0.5 h-4 w-4 shrink-0 text-[#8b7846]"
            ),
            rx.el.p(
                "Ao enviar, seu pedido será registrado e aguardará atendimento. Nenhum pagamento será solicitado ou cobrado nesta etapa. Catálogo demonstrativo; a entrega não está confirmada.",
                class_name="text-xs leading-6 text-[#536059]",
            ),
            class_name="mt-5 flex gap-3 border-t border-[#deded3] pt-5",
        ),
        rx.el.button(
            rx.cond(
                CartState.submitting,
                rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                rx.icon("send", class_name="h-4 w-4"),
            ),
            rx.cond(
                CartState.submitting,
                "Enviando pedido…",
                "Enviar pedido · sem pagamento",
            ),
            type="submit",
            disabled=CartState.submitting | CartState.busy | CartState.loading,
            class_name="mt-6 flex min-h-12 w-full items-center justify-center gap-3 bg-[#0d231d] px-5 py-4 text-xs font-medium text-[#f5f1e8] hover:bg-[#05120e] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#8b7846] disabled:cursor-wait disabled:opacity-60",
        ),
        on_submit=CartState.place_order,
        reset_on_submit=False,
        no_validate=True,
        class_name="mt-10 border border-[#deded3] bg-[#f5f3eb] p-5 sm:p-8",
    )


def order_confirmation() -> rx.Component:
    return rx.el.section(
        rx.icon(
            "clipboard-check", class_name="mx-auto h-12 w-12 text-[#8b7846]"
        ),
        rx.el.p(
            "OBRIGADO PELA SUA ESCOLHA",
            class_name="mt-6 text-[10px] tracking-[0.2em] text-[#8b7846]",
        ),
        rx.el.h1(
            "Pedido recebido",
            class_name="mt-3 font-['Cormorant_Garamond'] text-5xl text-[#0d231d]",
        ),
        rx.el.p(
            f"Número do pedido: {CartState.order_number}",
            class_name="mt-5 text-sm font-semibold text-[#0d231d]",
        ),
        rx.el.p(
            "Pedido recebido/aguardando atendimento",
            class_name="mx-auto mt-4 w-fit border border-[#deded3] bg-[#f5f3eb] px-4 py-2 text-xs text-[#536059]",
        ),
        rx.el.p(
            f"Total registrado: {CartState.order_total} · Frete grátis",
            class_name="mt-6 text-sm text-[#0d231d]",
        ),
        rx.el.p(
            "Nenhum pagamento foi cobrado. Este registro não é uma confirmação de pagamento ou de envio. O pedido aguarda atendimento; não há prazo de entrega confirmado.",
            class_name="mx-auto mt-5 max-w-lg text-sm leading-7 text-[#536059]",
        ),
        rx.el.p(
            "Guarde o número do pedido. A sacola foi esvaziada após o registro.",
            class_name="mt-4 text-xs text-[#536059]",
        ),
        rx.el.a(
            "Continuar comprando",
            rx.icon("arrow-right", class_name="h-4 w-4"),
            href="/#catalogo",
            class_name="mx-auto mt-8 flex w-fit items-center gap-4 bg-[#0d231d] px-7 py-4 text-xs text-[#f5f1e8] hover:bg-[#05120e]",
        ),
        id="pedido-recebido",
        aria_live="polite",
        class_name="border border-[#deded3] bg-white px-5 py-16 text-center sm:px-10",
    )


def cart_contents() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(CartState.lines, cart_line),
            rx.el.a(
                rx.icon("arrow-left", class_name="h-4 w-4"),
                "Continuar comprando",
                href="/#catalogo",
                class_name="mt-6 flex w-fit items-center gap-3 text-xs text-[#0d231d] underline underline-offset-4 hover:text-[#8b7846]",
            ),
            checkout_form(),
            class_name="min-w-0 lg:col-span-2",
        ),
        rx.el.aside(
            rx.el.h2(
                "Resumo da sacola",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
            ),
            rx.el.div(
                rx.el.span("Subtotal"),
                rx.el.span(CartState.subtotal),
                class_name="mt-7 flex justify-between text-sm text-[#536059]",
            ),
            rx.el.div(
                rx.el.span("Frete"),
                rx.el.span("Grátis", class_name="font-medium text-[#0d231d]"),
                class_name="mt-4 flex justify-between text-sm text-[#536059]",
            ),
            rx.el.div(
                rx.el.span("Total"),
                rx.el.span(CartState.subtotal),
                class_name="mt-6 flex justify-between border-t border-[#deded3] pt-6 text-lg font-semibold text-[#0d231d]",
            ),
            rx.el.p(
                "Preços e disponibilidade serão conferidos novamente ao enviar o pedido. As peças não ficam reservadas na sacola.",
                class_name="mt-6 text-xs leading-6 text-[#536059]",
            ),
            rx.el.p(
                "Sem cobrança de pagamento nesta etapa.",
                class_name="mt-4 text-xs text-[#8b7846]",
            ),
            class_name="h-fit border border-[#deded3] bg-white p-6 sm:p-8 lg:sticky lg:top-8",
        ),
        class_name="grid w-full grid-cols-1 items-start gap-8 lg:grid-cols-3 lg:gap-12",
    )


def cart_content() -> rx.Component:
    return rx.el.div(
        rx.cond(
            CartState.confirmed,
            order_confirmation(),
            rx.el.div(
                rx.el.p(
                    "SUAS ESCOLHAS, EM CADA DETALHE",
                    class_name="text-[10px] tracking-[0.2em] text-[#8b7846]",
                ),
                rx.el.h1(
                    "Sua sacola",
                    class_name="mt-3 font-['Cormorant_Garamond'] text-5xl text-[#0d231d] sm:text-6xl",
                ),
                rx.el.p(
                    f"{CartState.count} unidades na sacola",
                    class_name="mt-3 text-xs text-[#536059]",
                ),
                rx.cond(
                    CartState.error != "",
                    rx.el.div(
                        rx.el.p(CartState.error),
                        rx.el.button(
                            "Atualizar sacola",
                            on_click=CartState.load_cart,
                            disabled=CartState.submitting | CartState.busy,
                            class_name="mt-2 bg-transparent text-xs text-red-700 underline underline-offset-4 disabled:opacity-40",
                        ),
                        role="alert",
                        class_name="mt-6 border border-red-200 bg-red-50 p-4 text-sm text-red-700",
                    ),
                ),
                rx.el.p(
                    CartState.notice,
                    role="status",
                    aria_live="polite",
                    class_name="mt-4 text-xs text-[#536059]",
                ),
                rx.cond(
                    CartState.loading,
                    rx.el.div(
                        rx.el.p(
                            "Carregando sua sacola…",
                            class_name="text-sm text-[#536059]",
                        ),
                        role="status",
                        class_name="mt-8 h-64 animate-pulse border border-[#deded3] bg-[#edece3] p-8",
                    ),
                    rx.cond(
                        CartState.count > 0,
                        cart_contents(),
                        rx.el.div(
                            rx.icon(
                                "shopping-bag",
                                class_name="mx-auto h-10 w-10 text-[#8b7846]",
                            ),
                            rx.el.h2(
                                "Sua sacola está vazia",
                                class_name="mt-5 font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
                            ),
                            rx.el.p(
                                "Encontre uma peça especial para o seu dia a dia.",
                                class_name="mt-3 text-sm text-[#536059]",
                            ),
                            rx.el.a(
                                "Explorar a coleção",
                                href="/#catalogo",
                                class_name="mx-auto mt-7 block w-fit bg-[#0d231d] px-7 py-4 text-xs text-[#f5f1e8] hover:bg-[#05120e]",
                            ),
                            class_name="mt-8 border border-[#deded3] bg-white px-5 py-16 text-center",
                        ),
                    ),
                ),
            ),
        ),
        class_name="mx-auto w-full max-w-[1440px] px-6 py-12 lg:px-12 lg:py-16",
    )
