import reflex as rx
import logging
from sqlalchemy import select, text
from app.models import Product


async def seed_catalog():
    try:
        async with rx.asession() as session:
            # Serialize empty-table seeding across workers without changing the schema.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(71420931)")
            )
            if await session.scalar(select(Product.id).limit(1)) is not None:
                return
            catalog = (
                (
                    "Vestido midi de linho",
                    "Vestido midi em tom natural, com cintura marcada e caimento leve. Uma proposta para dias de sol e encontros especiais.",
                    "Feminino",
                    "photo-1515372039744-b8f02a3ae446",
                    32990,
                    None,
                    "Novidade",
                ),
                (
                    "Bolsa tiracolo caramelo",
                    "Bolsa compacta em tom caramelo, com alça longa e espaço para os essenciais do dia a dia.",
                    "Acessórios",
                    "photo-1548036328-c9fa89d128fa",
                    24990,
                    29990,
                    "Seleção especial",
                ),
                (
                    "Camisa essencial branca",
                    "Camisa branca de manga longa com corte clássico. Uma peça versátil para composições casuais ou elegantes.",
                    "Masculino",
                    "photo-1596755094514-f87e34085b2c",
                    18990,
                    None,
                    "Essencial",
                ),
                (
                    "Tricô de textura suave",
                    "Tricô de mangas longas com textura aconchegante e modelagem confortável para sobreposições.",
                    "Feminino",
                    "photo-1434389677669-e08b4cac3105",
                    27990,
                    None,
                    "Novidade",
                ),
                (
                    "Relógio clássico dourado",
                    "Relógio analógico com acabamento dourado e desenho atemporal. Um detalhe marcante para o cotidiano.",
                    "Acessórios",
                    "photo-1524805444758-089113d48a6d",
                    45990,
                    None,
                    "Destaque",
                ),
                (
                    "Tênis urbano branco",
                    "Tênis de perfil baixo em branco, com linhas limpas e proposta casual para combinar com seus básicos.",
                    "Masculino",
                    "photo-1549298916-b41d501d3772",
                    29990,
                    35990,
                    "Promoção",
                ),
                (
                    "Óculos de sol essencial",
                    "Óculos de sol com armação de inspiração clássica. Um acessório para completar looks de verão.",
                    "Acessórios",
                    "photo-1511499767150-a48a237f0083",
                    15990,
                    None,
                    "Essencial",
                ),
                (
                    "Jaqueta denim clássica",
                    "Jaqueta jeans de lavagem azul, com bolsos frontais e corte descontraído. Feita para compor camadas.",
                    "Feminino",
                    "photo-1543076447-215ad9ba6923",
                    38990,
                    44990,
                    "Promoção",
                ),
            )
            for index, (
                title,
                description,
                category,
                photo,
                price,
                compare,
                badge,
            ) in enumerate(catalog):
                session.add(
                    Product(
                        sku=f"DEMO-EDITORIAL-{index + 1:03d}",
                        title=title,
                        description=description,
                        category=category,
                        image_url=f"https://images.unsplash.com/{photo}?auto=format&fit=crop&w=900&q=85",
                        price_centavos=price,
                        compare_at_price_centavos=compare,
                        badge=badge,
                        featured=index < 4,
                        stock=0 if index == 7 else 15,
                    )
                )
            await session.commit()
    except Exception as e:
        logging.exception(f"Error: {e}")
        raise
