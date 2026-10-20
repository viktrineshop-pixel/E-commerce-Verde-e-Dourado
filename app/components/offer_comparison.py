import reflex as rx
from app.public_catalog import OfferView
from app.click_tracking import offer_tracking_url


def offer_row(offer: OfferView) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.strong(
                offer["merchant"], class_name="text-sm text-[#073238]"
            ),
            rx.el.span(
                offer["price"],
                class_name="text-base font-semibold text-[#073238]",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(offer["comparison"], class_name="mt-2 text-xs text-[#0B4146]"),
        rx.el.p(
            f"Fonte: {offer['source']}",
            class_name="mt-2 break-words text-xs text-gray-600",
        ),
        rx.el.p(
            f"Observado em {offer['observed']}",
            class_name="mt-1 break-words text-xs text-gray-600",
        ),
        rx.el.a(
            "Ir para a loja",
            rx.icon("arrow-up-right", class_name="h-4 w-4"),
            href=offer_tracking_url(offer["id"]),
            rel="nofollow sponsored",
            aria_label=f"Ir para {offer['merchant']} por link de afiliado",
            class_name="mt-3 flex min-h-11 items-center justify-center gap-2 border border-[#d4af37] bg-[#d4af37] px-4 py-2 text-xs font-semibold text-[#073238] hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#073238]",
        ),
        rx.el.p(
            offer["disclosure"],
            class_name="mt-3 text-xs leading-5 text-gray-600",
        ),
        key=offer["id"],
        class_name="border-t border-[#dedfd5] py-4 text-[#073238]",
    )


def offer_evidence(offer: OfferView) -> rx.Component:
    return rx.el.article(
        offer_row(offer),
        rx.el.p(
            f"Oferta atualizada: {offer['updated']} · Link revisado manualmente: {offer['checked']}",
            class_name="text-xs leading-6 text-gray-600",
        ),
        rx.el.h3(
            "Histórico observado",
            class_name="mt-5 font-semibold text-[#073238]",
        ),
        rx.el.p(
            offer["history_note"],
            class_name="mt-2 text-xs leading-6 text-gray-600",
        ),
        rx.cond(
            offer["history"].length() >= 2,
            rx.el.ol(
                rx.foreach(
                    offer["history"],
                    lambda item: rx.el.li(
                        item,
                        class_name="border-b border-gray-200 py-3 text-xs text-gray-600",
                    ),
                ),
                class_name="mt-3",
            ),
        ),
        rx.cond(
            offer["terms"].length() > 0,
            rx.el.div(
                rx.el.h3(
                    "Campanhas informativas desta loja/oferta",
                    class_name="mt-5 font-semibold text-[#073238]",
                ),
                rx.foreach(
                    offer["terms"],
                    lambda term: rx.el.p(
                        term,
                        class_name="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-600",
                    ),
                ),
            ),
        ),
        key=offer["id"],
        class_name="border border-[#dedfd5] bg-white p-5 text-[#073238]",
    )
