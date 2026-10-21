import reflex as rx
from app.states.admin_coupon_state import AdminCouponState, CouponRow


def coupon_field(
    name: str, label: str, placeholder: str, input_type: str = "text"
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"coupon-{name}",
            class_name="mb-2 block text-xs font-medium text-[#073238]",
        ),
        rx.el.input(
            id=f"coupon-{name}",
            name=name,
            type=input_type,
            placeholder=placeholder,
            default_value=AdminCouponState.draft[name],
            key=AdminCouponState.draft[name],
            disabled=AdminCouponState.busy | AdminCouponState.loading,
            max_length=100,
            aria_invalid=AdminCouponState.errors.get(name, "") != "",
            aria_describedby=f"coupon-{name}-error",
            class_name="min-h-11 w-full rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 text-sm text-[#073238] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
        ),
        rx.el.p(
            AdminCouponState.errors.get(name, ""),
            id=f"coupon-{name}-error",
            class_name="mt-1 text-xs text-red-700",
        ),
        class_name="min-w-0",
    )


def coupon_editor() -> rx.Component:
    return rx.el.form(
        rx.el.h3(
            rx.cond(AdminCouponState.editing, "Editar cupom", "Novo cupom"),
            class_name="font-['Cormorant_Garamond'] text-2xl text-[#073238]",
        ),
        rx.el.div(
            coupon_field("code", "Código *", "BOAS-VINDAS"),
            rx.el.div(
                rx.el.label(
                    "Tipo de desconto *",
                    html_for="coupon-kind",
                    class_name="mb-2 block text-xs font-medium text-[#073238]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("Percentual (1–100%)", value="percent"),
                        rx.el.option("Valor fixo em BRL", value="fixed"),
                        name="kind",
                        id="coupon-kind",
                        default_value=AdminCouponState.draft["kind"],
                        disabled=AdminCouponState.busy
                        | AdminCouponState.loading,
                        class_name="min-h-11 w-full appearance-none rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 pr-9 text-sm text-[#073238] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
                    ),
                    rx.icon(
                        "chevron-down",
                        aria_hidden=True,
                        class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#073238]",
                    ),
                    class_name="relative",
                ),
            ),
            coupon_field("value", "Valor * (% inteiro ou R$)", "10 ou 20,00"),
            coupon_field("expires", "Validade (opcional)", "", "date"),
            class_name="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2",
        ),
        rx.el.label(
            rx.el.input(
                type="checkbox",
                name="active",
                default_checked=AdminCouponState.active,
                disabled=AdminCouponState.busy | AdminCouponState.loading,
                class_name="h-4 w-4 accent-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            "Registro legado ativo (sem aplicação em compras)",
            class_name="mt-4 flex min-h-11 items-center gap-3 text-xs text-[#073238]",
        ),
        rx.el.p(
            "Estes campos preservam as regras do cadastro legado. Ativar ou editar não publica um cupom de loja externa nem habilita aplicação de desconto na Viktrine.",
            class_name="mt-2 text-xs leading-6 text-[#596559]",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("save", class_name="h-4 w-4"),
                rx.cond(AdminCouponState.busy, "Processando…", "Salvar cupom"),
                type="submit",
                disabled=AdminCouponState.busy | AdminCouponState.loading,
                class_name="flex min-h-11 items-center gap-2 rounded-sm bg-[#073238] px-4 text-xs text-[#faf9f4] hover:bg-[#0d231d] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.el.button(
                "Novo / limpar",
                type="button",
                on_click=AdminCouponState.new_coupon,
                disabled=AdminCouponState.busy | AdminCouponState.loading,
                class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="mt-4 flex flex-wrap gap-3",
        ),
        on_submit=AdminCouponState.save_coupon,
        no_validate=True,
        reset_on_submit=False,
        key=AdminCouponState.revision,
        class_name="min-w-0 rounded-sm border border-[#deded3] bg-white p-5",
    )


def coupon_row(c: CouponRow) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.h3(
                c["code"],
                class_name="break-all text-sm font-semibold text-[#073238]",
            ),
            rx.el.p(
                f"{c['benefit']} · {c['validity']}",
                class_name="mt-1 text-xs text-[#596559]",
            ),
            rx.el.div(
                rx.el.span(
                    rx.cond(c["active"], "Ativo", "Desativado"),
                    class_name="w-fit rounded-full border border-[#d8d7cc] bg-[#faf9f4] px-2 py-1 text-xs text-[#073238]",
                ),
                rx.cond(
                    c["expired"],
                    rx.el.span(
                        "Expirado",
                        class_name="w-fit rounded-full bg-yellow-100 px-2 py-1 text-xs text-yellow-800",
                    ),
                ),
                class_name="mt-2 flex flex-wrap gap-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                "Editar",
                type="button",
                on_click=AdminCouponState.edit_coupon(c["id"]),
                aria_label=f"Editar cupom {c['code']}",
                disabled=AdminCouponState.busy | AdminCouponState.loading,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.el.button(
                rx.cond(c["active"], "Desativar", "Ativar"),
                type="button",
                on_click=AdminCouponState.set_active(c["id"], ~c["active"]),
                aria_label=f"Alterar ativação do cupom {c['code']}",
                disabled=AdminCouponState.busy | AdminCouponState.loading,
                class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap gap-2",
        ),
        key=c["id"],
        class_name="flex flex-wrap items-center gap-4 border-b border-[#deded3] py-4 last:border-b-0",
    )


def admin_coupons() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                rx.icon("ticket-percent", class_name="h-6 w-6 text-[#8b7846]"),
                "Cupons locais legados",
                class_name="flex items-center gap-3 font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Atualizar cupons",
                type="button",
                on_click=AdminCouponState.load_coupons(0),
                disabled=AdminCouponState.loading | AdminCouponState.busy,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            "Registros locais da antiga demonstração, não cupons das lojas externas. A Viktrine não aplica descontos nem possui checkout. Cupons informativos de lojas são cadastrados na curadoria editorial com fonte e condições; o arquivo de pedidos permanece intacto.",
            class_name="mt-3 text-xs leading-6 text-[#596559]",
        ),
        rx.cond(
            AdminCouponState.error != "",
            rx.el.p(
                AdminCouponState.error,
                role="alert",
                class_name="mt-4 border border-red-200 bg-red-50 p-3 text-sm text-red-700",
            ),
        ),
        rx.cond(
            AdminCouponState.notice != "",
            rx.el.p(
                AdminCouponState.notice,
                role="status",
                class_name="mt-4 border border-green-200 bg-green-50 p-3 text-sm text-green-700",
            ),
        ),
        rx.el.div(
            coupon_editor(),
            rx.el.div(
                rx.cond(
                    AdminCouponState.loading,
                    rx.el.p(
                        "Carregando cupons…",
                        role="status",
                        class_name="animate-pulse bg-[#faf9f4] p-5 text-sm text-[#596559]",
                    ),
                    rx.cond(
                        AdminCouponState.rows.length() > 0,
                        rx.foreach(AdminCouponState.rows, coupon_row),
                        rx.cond(
                            AdminCouponState.error == "",
                            rx.el.p(
                                "Nenhum cupom cadastrado nesta página. Crie um cupom ao lado.",
                                class_name="border border-dashed border-[#d8d7cc] bg-[#faf9f4] p-5 text-sm text-[#596559]",
                            ),
                        ),
                    ),
                ),
                rx.el.nav(
                    rx.el.button(
                        "Anterior",
                        type="button",
                        on_click=AdminCouponState.load_coupons(-1),
                        disabled=(AdminCouponState.page <= 1)
                        | AdminCouponState.loading
                        | AdminCouponState.busy,
                        class_name="min-h-11 bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
                    ),
                    rx.el.span(
                        f"Página {AdminCouponState.page}",
                        class_name="text-xs text-[#596559]",
                    ),
                    rx.el.button(
                        "Próxima",
                        type="button",
                        on_click=AdminCouponState.load_coupons(1),
                        disabled=(~AdminCouponState.has_next)
                        | AdminCouponState.loading
                        | AdminCouponState.busy,
                        class_name="min-h-11 bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
                    ),
                    aria_label="Paginação dos cupons",
                    class_name="mt-4 flex items-center justify-between gap-3",
                ),
                class_name="min-w-0",
            ),
            class_name="mt-5 grid w-full grid-cols-1 items-start gap-6 xl:grid-cols-2",
        ),
        aria_busy=AdminCouponState.loading | AdminCouponState.busy,
        class_name="mb-6 w-full rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )
