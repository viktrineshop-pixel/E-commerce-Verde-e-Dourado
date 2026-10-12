import reflex as rx
import os
from collections.abc import Sequence
import reflex_enterprise as rxe
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
            # Browsers treat \ as / and strip tab/CR/LF in URLs, so
            # "/\host" and "/\t/host" both become "//host".
            and not any(c in raw for c in "\t\r\n\\")
            else "/"
        )
        return rx.redirect(target)


def login_page(*, providers: Sequence, **context) -> rx.Component:
    return rx.fragment(
        rx.el.main(
            rx.el.a(
                "VIKTRINE SHOP",
                href="/",
                class_name="mb-12 whitespace-nowrap font-['Cormorant_Garamond'] text-3xl font-semibold tracking-[0.12em] text-[#d4af37] sm:text-4xl focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.div(
                rx.icon(
                    "user-round",
                    class_name="mx-auto mb-6 h-7 w-7 text-[#a68c3a]",
                ),
                rx.el.p(
                    "BEM-VINDO DE VOLTA",
                    class_name="text-[10px] tracking-[0.22em] text-[#8b7846]",
                ),
                rx.el.h1(
                    "Seu estilo, seu espaço.",
                    class_name="mt-4 font-['Cormorant_Garamond'] text-4xl text-[var(--brand-petroleum)]",
                ),
                rx.el.p(
                    "Entre com sua conta para continuar. A vitrine está sempre aberta para você explorar.",
                    class_name="mt-5 text-sm leading-relaxed text-[#687268]",
                ),
                *[
                    provider.get_login_button(
                        rx.el.button(
                            _LOGIN_LABEL,
                            rx.icon("arrow-right", class_name="h-4 w-4"),
                            class_name="mt-8 flex w-full items-center justify-center gap-3 bg-[var(--brand-petroleum)] px-6 py-4 text-sm text-[#f5f1e8] transition-colors hover:bg-[var(--brand-petroleum-deep)] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
                        ),
                    )
                    for provider in providers
                ],
                rx.el.a(
                    "Voltar à vitrine",
                    href="/",
                    class_name="mt-7 inline-block text-xs text-[#687268] underline underline-offset-4 hover:text-[var(--brand-petroleum)]",
                ),
                class_name="w-full max-w-md border border-[#d4af37]/25 bg-[#faf9f4] px-8 py-12 text-center md:px-12",
            ),
            rx.el.p(
                "Elegância nos pequenos detalhes.",
                class_name="mt-10 font-['Cormorant_Garamond'] text-xl italic text-[#c5bea8]",
            ),
            class_name="flex min-h-dvh flex-col items-center justify-center bg-[var(--brand-petroleum-deep)] px-6 py-16 font-['Inter'] text-[#faf9f4]",
        ),
        rx.cond(
            AuthUserState.provider_name != "",
            rx.el.div(on_mount=LoginRedirectState.continue_to_app),
        ),
    )
