import reflex as rx
import reflex_enterprise as rxe
import os
from collections.abc import Sequence
from reflex_enterprise.auth import AuthUserState


_PROVIDER_NAME = os.environ.get("OIDC_PROVIDER_NAME", "")
_LOGIN_LABEL = (
    f"Continue with {_PROVIDER_NAME}" if _PROVIDER_NAME else "Sign in"
)


class LoginRedirectState(rx.State):
    @rxe.event(auth=False)
    def continue_to_app(self):
        raw = self.router.page.params.get("redirect_to", "/")
        target = (
            raw
            if isinstance(raw, str)
            and raw.startswith("/")
            and not raw.startswith("//")
            and not any(c in raw for c in "\t\r\n\\")
            else "/"
        )
        return rx.redirect(target)


def provider_button(provider) -> rx.Component:
    return provider.get_login_button(
        rx.el.button(
            rx.icon("log-in", class_name="h-4 w-4"),
            _LOGIN_LABEL,
            type="button",
            class_name="flex w-full items-center justify-center gap-3 border border-[#d4af37] bg-[#073238] px-6 py-4 text-sm font-medium text-[#faf9f4] transition-colors hover:bg-[#0c454d] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
        )
    )


def login_page(*, providers: Sequence, **context) -> rx.Component:
    return rx.fragment(
        rx.el.main(
            rx.el.div(
                rx.el.a(
                    rx.el.span("Viktrine", class_name="block leading-none"),
                    href="/",
                    aria_label="Viktrine — página inicial",
                    class_name="inline-block font-['Cormorant_Garamond'] text-5xl font-medium tracking-[0.1em] text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.section(
                    rx.icon(
                        "user-round",
                        class_name="mx-auto h-7 w-7 text-[#8b7846]",
                    ),
                    rx.el.p(
                        "UM ESPAÇO SÓ SEU",
                        class_name="mt-6 text-[10px] tracking-[0.22em] text-[#71602f]",
                    ),
                    rx.el.h1(
                        "Bem-vindo à sua vitrine.",
                        class_name="mt-3 font-['Cormorant_Garamond'] text-4xl font-medium text-[#073238]",
                    ),
                    rx.el.p(
                        "Entre para salvar favoritos, organizar listas privadas e consultar o arquivo demonstrativo de pedidos anteriores. A Viktrine encaminha ofertas; compras são feitas nas lojas externas.",
                        class_name="mt-4 text-sm leading-7 text-[#52615b]",
                    ),
                    rx.el.div(
                        *map(provider_button, providers),
                        class_name="mt-8 flex flex-col gap-3",
                    ),
                    rx.el.a(
                        "Continuar descobrindo ofertas",
                        href="/",
                        class_name="mt-6 inline-block text-xs text-[#073238] underline underline-offset-4 hover:text-[#71602f] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                    class_name="mt-10 w-full border border-[#d4af37]/35 bg-[#faf9f4] px-6 py-10 sm:px-10",
                ),
                class_name="w-full max-w-md text-center",
            ),
            class_name="flex min-h-dvh w-full items-center justify-center bg-[#073238] px-6 py-12 font-['Inter'] text-[#faf9f4]",
        ),
        rx.cond(
            AuthUserState.provider_name != "",
            rx.el.div(on_mount=LoginRedirectState.continue_to_app),
        ),
    )
