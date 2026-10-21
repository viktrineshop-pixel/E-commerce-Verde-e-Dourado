import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import Any
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.models import MediaProvaSocial
from app.states.authorization import is_admin
from app.landing_products import (
    LandingView,
    LandingMedia,
    MAX_FILE_BYTES,
    MAX_BATCH_BYTES,
    MEDIA_TYPES,
    normalize_slug,
    unique_slug,
    safe_landing_url,
    valid_media,
)


class LandingAdminState(rx.State):
    products: list[LandingView] = rxe.field([], auth=is_admin)
    draft: dict[str, str] = rxe.field(
        {"nome": "", "descricao": "", "url": "", "slug": ""}, auth=is_admin
    )
    editing_id: int = rxe.field(0, auth=is_admin)
    busy: bool = rxe.field(False, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    page: int = rxe.field(1, auth=is_admin)
    total: int = rxe.field(0, auth=is_admin)
    revision: int = rxe.field(0, auth=is_admin)
    _pending: list[tuple[str, str, bytes]] = []
    _upload_product_id: int = 0
    _save_fields: dict[str, str] = {}

    @rxe.event(auth=is_admin, background=True)
    async def load_products(self):
        async with self:
            page = self.page
        try:
            async with rx.asession() as session:
                total = int(
                    await session.scalar(text("SELECT count(*) FROM produtos"))
                    or 0
                )
                rows = (
                    (
                        await session.execute(
                            text(
                                "SELECT id, nome, descricao, slug, published, link_afiliado_original FROM produtos ORDER BY id DESC LIMIT 20 OFFSET :offset"
                            ),
                            {"offset": (page - 1) * 20},
                        )
                    )
                    .mappings()
                    .all()
                )
                media_rows = (
                    (
                        await session.execute(
                            text(
                                "SELECT m.id, m.produto_id, m.tipo, m.content_type, m.filename, m.url_ficheiro FROM media_prova_social m JOIN (SELECT id FROM produtos ORDER BY id DESC LIMIT 20 OFFSET :offset) p ON p.id = m.produto_id ORDER BY m.position, m.id"
                            ),
                            {"offset": (page - 1) * 20},
                        )
                    )
                    .mappings()
                    .all()
                )
            products = [
                LandingView(
                    id=p["id"],
                    nome=p["nome"],
                    descricao=p["descricao"],
                    slug=p["slug"],
                    url=p["link_afiliado_original"],
                    published=p["published"],
                    media=[
                        LandingMedia(
                            id=m["id"],
                            tipo=m["tipo"],
                            content_type=m["content_type"],
                            filename=m["filename"] or "Mídia",
                            url=m["url_ficheiro"],
                        )
                        for m in media_rows
                        if m["produto_id"] == p["id"]
                    ],
                )
                for p in rows
            ]
            async with self:
                self.products = products
                self.total = total
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.products = []
                self.error = (
                    "Não foi possível carregar os produtos. Tente atualizar."
                )

    @rxe.event(auth=is_admin)
    def change_page(self, delta: int):
        self.page = min(
            max(1, (self.total + 19) // 20), max(1, self.page + delta)
        )
        return LandingAdminState.load_products

    @rxe.event(auth=is_admin)
    def new_draft(self):
        if self.busy:
            return
        self.editing_id = 0
        self.draft = {"nome": "", "descricao": "", "url": "", "slug": ""}
        self.revision += 1
        self.error = ""
        self.notice = ""

    @rxe.event(auth=is_admin, background=True)
    async def edit_product(self, product_id: int):
        async with self:
            if self.busy:
                return
        try:
            async with rx.asession() as session:
                row = (
                    (
                        await session.execute(
                            text(
                                "SELECT id, nome, descricao, slug, link_afiliado_original FROM produtos WHERE id = :id LIMIT 1"
                            ),
                            {"id": product_id},
                        )
                    )
                    .mappings()
                    .first()
                )
            if row is None:
                raise ValueError("Produto não encontrado.")
            async with self:
                self.editing_id = row["id"]
                self.draft = {
                    "nome": row["nome"],
                    "descricao": row["descricao"],
                    "url": row["link_afiliado_original"],
                    "slug": row["slug"],
                }
                self.revision += 1
                self.error = ""
                self.notice = "Alterações e novas mídias retornam o produto a rascunho para nova revisão."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Não foi possível abrir o produto. Atualize a lista."
                )

    @rxe.event(auth=is_admin, background=True)
    async def generate_slug(self, name: str):
        try:
            base = normalize_slug(name)
            async with self:
                editing = self.editing_id
            async with rx.asession() as session:
                slugs = set(
                    (
                        await session.execute(
                            text(
                                "SELECT slug FROM produtos WHERE id <> :id AND (slug = :base OR slug LIKE :prefix)"
                            ),
                            {
                                "id": editing,
                                "base": base,
                                "prefix": f"{base[:240]}%",
                            },
                        )
                    )
                    .scalars()
                    .all()
                )
            slug = unique_slug(base, slugs)
            yield rx.call_script(
                f"document.getElementById('landing-slug').value = {__import__('json').dumps(slug)}"
            )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Informe um nome válido para gerar o slug."

    @rxe.event(auth=is_admin)
    def save_form(self, form_data: dict[str, Any]):
        if self.busy:
            return
        self._save_fields = {
            key: str(form_data.get(key, "")).strip()
            for key in ("nome", "descricao", "url", "slug")
        }
        self.busy = True
        self.error = ""
        self.notice = ""
        yield LandingAdminState.persist_product

    @rxe.event(auth=is_admin, background=True)
    async def persist_product(self):
        async with self:
            fields = dict(self._save_fields)
            editing = self.editing_id
        try:
            if (
                not fields["nome"]
                or len(fields["nome"]) > 250
                or not fields["descricao"]
                or len(fields["descricao"]) > 10000
            ):
                raise ValueError(
                    "Nome obrigatório (até 250 caracteres) e descrição obrigatória (até 10.000)."
                )
            if not safe_landing_url(fields["url"]):
                raise ValueError(
                    "Informe uma URL HTTPS segura, sem credenciais, controles ou destinos locais/privados (até 2048 caracteres)."
                )
            slug = normalize_slug(fields["slug"] or fields["nome"])
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        text("SELECT pg_advisory_xact_lock(71420933)")
                    )
                    if not fields["slug"]:
                        existing = set(
                            (
                                await session.execute(
                                    text(
                                        "SELECT slug FROM produtos WHERE id <> :id AND slug LIKE :prefix"
                                    ),
                                    {"id": editing, "prefix": f"{slug[:240]}%"},
                                )
                            )
                            .scalars()
                            .all()
                        )
                        slug = unique_slug(slug, existing)
                    values = {**fields, "slug": slug, "id": editing}
                    if editing:
                        result = await session.execute(
                            text(
                                "UPDATE produtos SET nome = :nome, descricao = :descricao, slug = :slug, link_afiliado_original = :url, published = false, updated_at = now() WHERE id = :id RETURNING id"
                            ),
                            values,
                        )
                    else:
                        result = await session.execute(
                            text(
                                "INSERT INTO produtos (nome, descricao, slug, link_afiliado_original, published) VALUES (:nome, :descricao, :slug, :url, false) RETURNING id"
                            ),
                            values,
                        )
                    product_id = result.scalar_one_or_none()
                    if product_id is None:
                        raise ValueError("Produto não encontrado.")
            async with self:
                self.editing_id = product_id
                self.draft = {**fields, "slug": slug}
                self.revision += 1
                self.notice = "Rascunho salvo. Revise o conteúdo, o destino e as mídias antes de publicar."
            yield LandingAdminState.load_products
        except IntegrityError as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Este slug já está em uso. Edite-o ou gere outro; nada foi salvo."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível salvar. Nenhuma alteração foi confirmada."
                )
        finally:
            async with self:
                self.busy = False
                self._save_fields = {}

    @rxe.event(auth=is_admin, background=True)
    async def set_publication(self, product_id: int, publish: bool):
        async with self:
            if self.busy:
                return
            self.busy = True
            self.error = ""
        try:
            async with rx.asession() as session:
                async with session.begin():
                    p = (
                        (
                            await session.execute(
                                text(
                                    "SELECT nome, descricao, slug, link_afiliado_original FROM produtos WHERE id = :id FOR UPDATE"
                                ),
                                {"id": product_id},
                            )
                        )
                        .mappings()
                        .first()
                    )
                    if p is None:
                        raise ValueError("Produto não encontrado.")
                    if publish:
                        if (
                            not p["nome"].strip()
                            or not p["descricao"].strip()
                            or not safe_landing_url(p["link_afiliado_original"])
                            or normalize_slug(p["slug"]) != p["slug"]
                        ):
                            raise ValueError(
                                "Revise e corrija os dados antes de publicar."
                            )
                        media = (
                            (
                                await session.execute(
                                    text(
                                        "SELECT file_bytes, content_type, tipo, id, url_ficheiro FROM media_prova_social WHERE produto_id = :id"
                                    ),
                                    {"id": product_id},
                                )
                            )
                            .mappings()
                            .all()
                        )
                        if any(
                            m["file_bytes"] is None
                            or MEDIA_TYPES.get(m["content_type"]) != m["tipo"]
                            or not valid_media(
                                bytes(m["file_bytes"]), m["content_type"]
                            )
                            or m["url_ficheiro"]
                            != f"/media/prova-social/{m['id']}"
                            for m in media
                        ):
                            raise ValueError(
                                "Há mídia inválida. Remova-a antes de publicar."
                            )
                    await session.execute(
                        text(
                            "UPDATE produtos SET published = :published, updated_at = now() WHERE id = :id"
                        ),
                        {"published": publish, "id": product_id},
                    )
            async with self:
                self.notice = (
                    "Publicado após sua confirmação de revisão."
                    if publish
                    else "Despublicado. Página e mídias não estão disponíveis ao público."
                )
            yield LandingAdminState.load_products
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível alterar a publicação."
                )
        finally:
            async with self:
                self.busy = False

    @rxe.event(auth=is_admin)
    async def upload_media(self, files: list[rx.UploadFile]):
        if self.busy:
            return
        self.error = ""
        try:
            if not self.editing_id:
                raise ValueError(
                    "Salve ou selecione um produto antes de enviar mídias."
                )
            if not 1 <= len(files) <= 6:
                raise ValueError("Envie de 1 a 6 arquivos por vez.")
            pending: list[tuple[str, str, bytes]] = []
            total = 0
            for file in files:
                data = await file.read(MAX_FILE_BYTES + 1)
                content_type = (file.content_type or "").lower().strip()
                if not valid_media(data, content_type):
                    raise ValueError(
                        "Arquivo inválido: use JPEG, PNG, WebP, MP4 ou WebM real, até 15 MiB por arquivo."
                    )
                total += len(data)
                if total > MAX_BATCH_BYTES:
                    raise ValueError("O lote deve ter no máximo 40 MiB.")
                name = (
                    str(file.name or "midia").replace("\\", "/").split("/")[-1]
                )
                name = (
                    "".join(c for c in name if c.isprintable()).strip()[:255]
                    or "midia"
                )
                pending.append((name, content_type, data))
            self._pending = pending
            self._upload_product_id = self.editing_id
            self.busy = True
            yield LandingAdminState.persist_media
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "Não foi possível receber os arquivos."
            )
        finally:
            for file in files:
                await file.close()

    @rxe.event(auth=is_admin, background=True)
    async def persist_media(self):
        async with self:
            pending = self._pending
            product_id = self._upload_product_id
        try:
            async with rx.asession() as session:
                async with session.begin():
                    exists = await session.scalar(
                        text(
                            "SELECT id FROM produtos WHERE id = :id FOR UPDATE"
                        ),
                        {"id": product_id},
                    )
                    if exists is None:
                        raise ValueError(
                            "Produto não encontrado. Nenhuma mídia foi salva."
                        )
                    position = int(
                        await session.scalar(
                            text(
                                "SELECT COALESCE(max(position), -1) + 1 FROM media_prova_social WHERE produto_id = :id"
                            ),
                            {"id": product_id},
                        )
                    )
                    for offset, (name, mime, data) in enumerate(pending):
                        media_id = int(
                            await session.scalar(
                                text(
                                    "SELECT nextval(pg_get_serial_sequence('media_prova_social','id'))"
                                )
                            )
                        )
                        media = MediaProvaSocial(
                            produto_id=product_id,
                            tipo=MEDIA_TYPES[mime],
                            content_type=mime,
                            filename=name,
                            file_bytes=data,
                            position=position + offset,
                            url_ficheiro=f"/media/prova-social/{media_id}",
                        )
                        media.id = media_id
                        session.add(media)
                    await session.flush()
                    await session.execute(
                        text(
                            "UPDATE produtos SET published = false, updated_at = now() WHERE id = :id"
                        ),
                        {"id": product_id},
                    )
            async with self:
                self.notice = "Mídias salvas; produto em rascunho para revisão antes da publicação."
            yield rx.clear_selected_files("landing-media")
            yield LandingAdminState.load_products
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Falha no envio. O lote inteiro foi cancelado; nenhuma mídia foi salva."
                )
        finally:
            async with self:
                self._pending = []
                self._upload_product_id = 0
                self.busy = False

    @rxe.event(auth=is_admin, background=True)
    async def remove_media(self, product_id: int, media_id: int):
        async with self:
            if self.busy:
                return
            self.busy = True
        try:
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        text(
                            "SELECT id FROM produtos WHERE id = :id FOR UPDATE"
                        ),
                        {"id": product_id},
                    )
                    await session.execute(
                        text(
                            "DELETE FROM media_prova_social WHERE id = :media AND produto_id = :id"
                        ),
                        {"media": media_id, "id": product_id},
                    )
                    await session.execute(
                        text(
                            "UPDATE produtos SET published = false, updated_at = now() WHERE id = :id"
                        ),
                        {"id": product_id},
                    )
            async with self:
                self.notice = "Mídia removida. Revise o produto e publique novamente quando estiver pronto."
            yield LandingAdminState.load_products
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Não foi possível remover a mídia."
        finally:
            async with self:
                self.busy = False
