import reflex as rx
import reflex_enterprise as rxe


class LegacyNavigationState(rx.State):
    @rxe.event(auth=False)
    def redirect_to_discovery(self):
        yield rx.toast(
            "A Viktrine não possui sacola ou checkout de produtos. Explore ofertas e compre nas lojas externas.",
            duration=7000,
        )
        yield rx.redirect("/")
