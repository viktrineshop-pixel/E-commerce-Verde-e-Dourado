import reflex as rx
from app.states.storefront_state import StorefrontState


def filter_select(
    name: str, label: str, values: rx.Var[list[str]], default: rx.Var[str]
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"filter-{name}",
            class_name="mb-2 block text-xs font-medium text-[#073238]",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    values, lambda value: rx.el.option(value, value=value)
                ),
                name=name,
                id=f"filter-{name}",
                default_value=default,
                key=default,
                class_name="min-h-11 w-full appearance-none border border-[#dedfd5] bg-white py-2 pr-8 pl-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#073238]",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-4 h-3 w-3 text-[#073238]",
            ),
            class_name="relative",
        ),
        class_name="min-w-0",
    )


def discovery_filters() -> rx.Component:
    return rx.el.form(
        filter_select(
            "category",
            "Categoria e descendentes",
            StorefrontState.categories,
            StorefrontState.category,
        ),
        rx.el.div(
            rx.el.label(
                "Loja",
                html_for="filter-merchant",
                class_name="mb-2 block text-xs font-medium text-[#073238]",
            ),
            rx.el.div(
                rx.el.select(
                    rx.el.option("Todas as lojas", value=""),
                    rx.foreach(
                        StorefrontState.merchants,
                        lambda m: rx.el.option(m, value=m),
                    ),
                    name="merchant",
                    id="filter-merchant",
                    default_value=StorefrontState.merchant,
                    key=StorefrontState.merchant,
                    class_name="min-h-11 w-full appearance-none border border-[#dedfd5] bg-white py-2 pr-8 pl-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#073238]",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="pointer-events-none absolute right-3 top-4 h-3 w-3 text-[#073238]",
                ),
                class_name="relative",
            ),
        ),
        rx.el.div(
            rx.el.label(
                "Mínimo em R$",
                html_for="price-minimum",
                class_name="mb-2 block text-xs text-[#073238]",
            ),
            rx.el.input(
                id="price-minimum",
                name="minimum",
                default_value=StorefrontState.minimum,
                key=StorefrontState.minimum,
                placeholder="Sem mínimo",
                class_name="min-h-11 w-full border border-[#dedfd5] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#073238]",
            ),
        ),
        rx.el.div(
            rx.el.label(
                "Máximo em R$",
                html_for="price-maximum",
                class_name="mb-2 block text-xs text-[#073238]",
            ),
            rx.el.input(
                id="price-maximum",
                name="maximum",
                default_value=StorefrontState.maximum,
                key=StorefrontState.maximum,
                placeholder="Sem máximo",
                class_name="min-h-11 w-full border border-[#dedfd5] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#073238]",
            ),
        ),
        filter_select(
            "sort",
            "Ordenação por moeda",
            rx.Var.create(["Mais recentes", "Menor preço", "Maior preço"]),
            StorefrontState.sort,
        ),
        rx.el.button(
            "Aplicar filtros",
            type="submit",
            class_name="min-h-11 self-end border border-[#d4af37] bg-[#073238] px-4 text-xs font-semibold text-white hover:bg-[#0B4146] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        on_submit=StorefrontState.apply_filters,
        class_name="my-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6",
    )
