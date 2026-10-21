import reflex as rx
from app.landing_products import LandingMedia, LandingView, media_url
from app.states.product_detail_state import ProductDetailState
from app.states.landing_catalog_state import LandingCatalogState


def landing_media(media: LandingMedia) -> rx.Component:
    return rx.el.figure(
        rx.cond(
            media["tipo"] == "image",
            rx.el.a(
                rx.el.img(
                    src=media_url(media["id"]),
                    alt=f"Imagem do produto fornecida pela administração: {media['filename']}",
                    loading="lazy",
                    class_name="aspect-square w-full bg-[#efede4] object-contain",
                ),
                href=media_url(media["id"]),
                target="_blank",
                rel="noopener noreferrer",
                aria_label="Abrir imagem do produto em nova aba",
                class_name="block focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.video(
                rx.el.source(
                    src=media_url(media["id"]), type=media["content_type"]
                ),
                "Seu navegador não suporta este vídeo.",
                controls=True,
                preload="metadata",
                aria_label=f"Vídeo do produto fornecido pela administração: {media['filename']}",
                class_name="aspect-square w-full bg-[#efede4] object-contain",
            ),
        ),
        rx.el.figcaption(
            "Material fornecido pela administração",
            class_name="mt-2 text-xs text-gray-600",
        ),
        key=media["id"],
        class_name="min-w-0",
    )


def landing_detail() -> rx.Component:
    return rx.el.section(
        rx.el.h1(
            ProductDetailState.landing["nome"],
            class_name="font-['Cormorant_Garamond'] text-4xl text-[#073238] md:text-5xl",
        ),
        rx.el.p(
            ProductDetailState.landing["descricao"],
            class_name="mt-5 whitespace-pre-wrap text-sm leading-7 text-gray-600",
        ),
        rx.el.div(
            rx.cond(
                ProductDetailState.landing["media"].length() > 0,
                rx.el.div(
                    rx.foreach(
                        ProductDetailState.landing["media"], landing_media
                    ),
                    class_name="grid gap-6 sm:grid-cols-2 lg:grid-cols-3",
                ),
                rx.el.div(
                    rx.icon("image", class_name="mb-3 h-7 w-7 text-[#8b7846]"),
                    rx.el.p(
                        "Nenhuma imagem ou vídeo foi fornecido para este produto.",
                        class_name="text-sm text-gray-600",
                    ),
                    class_name="border border-dashed border-[#d8d7cc] bg-white p-8",
                ),
            ),
            class_name="mt-8 w-full",
        ),
        rx.cond(
            ProductDetailState.landing["published"]
            & (ProductDetailState.landing["url"] != ""),
            rx.el.a(
                "Ir para a loja externa",
                rx.icon("external-link", class_name="h-4 w-4"),
                href=ProductDetailState.landing["url"],
                target="_blank",
                rel="nofollow sponsored noopener noreferrer",
                class_name="mt-5 inline-flex min-h-12 items-center justify-center gap-3 rounded-sm bg-[#073238] px-6 py-3 text-sm font-medium text-[#faf9f4] hover:bg-[#0B4146] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37]",
            ),
        ),
        rx.el.p(
            "Link de afiliado: a Viktrine pode receber uma comissão pelo encaminhamento. A compra, o pagamento e as condições comerciais ocorrem exclusivamente na loja externa, em uma nova aba.",
            class_name="mt-4 text-sm leading-6 text-gray-600",
        ),
        rx.el.p(
            "Imagens e vídeos foram fornecidos pela administração. Não são depoimentos de compradores verificados nem comprovação de compra, desempenho ou satisfação.",
            class_name="mt-3 text-xs leading-6 text-gray-600",
        ),
        class_name="mb-12 w-full text-[#073238]",
    )


def landing_catalog() -> rx.Component:
    return rx.el.div(
        rx.cond(
            LandingCatalogState.products.length() > 0,
            rx.el.section(
                rx.el.h2(
                    "Explore também",
                    class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238] md:text-4xl",
                ),
                rx.el.p(
                    "Páginas selecionadas pela administração, com encaminhamento por link de afiliado. Compras nas lojas externas.",
                    class_name="mt-3 text-sm leading-6 text-gray-600",
                ),
                rx.el.ul(
                    rx.foreach(
                        LandingCatalogState.products,
                        lambda product: rx.el.li(
                            rx.el.a(
                                product["nome"],
                                rx.icon(
                                    "arrow-right", class_name="h-4 w-4 shrink-0"
                                ),
                                href=f"/produto/{product['slug']}",
                                class_name="flex min-h-14 items-center justify-between gap-4 border-b border-[#dedfd5] py-4 text-sm text-[#073238] hover:underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                            ),
                            key=product["id"],
                        ),
                    ),
                    class_name="mt-5 grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3",
                ),
                class_name="mx-auto w-full max-w-[1440px] border-t border-[#dedfd5] px-6 py-12 lg:px-12",
            ),
        ),
        rx.cond(
            LandingCatalogState.error != "",
            rx.el.p(
                LandingCatalogState.error,
                role="status",
                class_name="mx-auto w-full max-w-[1440px] px-6 py-6 text-xs text-gray-600",
            ),
        ),
        on_mount=LandingCatalogState.load_products,
        class_name="w-full bg-[#faf9f4] text-[#073238]",
    )
