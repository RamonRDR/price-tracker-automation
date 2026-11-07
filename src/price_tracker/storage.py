"""SQLAlchemy repository with SQLite foreign keys and controlled transactions."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from price_tracker.errors import InvalidProduct
from price_tracker.models import AlertEvent, Base, PriceObservation, Product
from price_tracker.schemas import PriceQuote, ProductInput


class Store:
    def __init__(self, path: Path):
        path = path.expanduser().absolute()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.engine: Engine = create_engine(f"sqlite:///{path}", connect_args={"timeout": 15})
        event.listen(self.engine, "connect", self._set_pragmas)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    @staticmethod
    def _set_pragmas(connection: object, _: object) -> None:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def add(self, data: ProductInput) -> Product:
        url = str(data.url)
        with self.session() as session:
            if session.scalar(select(Product.id).where(Product.url == url)):
                raise InvalidProduct("This URL is already registered")
            product = Product(
                url=url,
                name=url,
                adapter=data.adapter,
                name_selector=data.name_selector,
                price_selector=data.price_selector,
                currency=data.currency,
                target=data.target,
                drop_percent=data.drop_percent,
            )
            session.add(product)
            session.flush()
            return product

    def get(self, product_id: int) -> Product:
        with self.session() as session:
            product = session.get(Product, product_id)
            if product is None:
                raise InvalidProduct(f"No product with ID {product_id}")
            return product

    def list_products(self, *, active_only: bool = False, limit: int = 500) -> list[Product]:
        with self.session() as session:
            query = select(Product).order_by(Product.id).limit(limit)
            if active_only:
                query = query.where(Product.active.is_(True))
            return list(session.scalars(query))

    def set_alerts(
        self, product_id: int, *, target: object = ..., drop_percent: object = ...
    ) -> Product:
        with self.session() as session:
            product = session.get(Product, product_id)
            if product is None:
                raise InvalidProduct(f"No product with ID {product_id}")
            if target is not ...:
                product.target = target  # type: ignore[assignment]
            if drop_percent is not ...:
                product.drop_percent = drop_percent  # type: ignore[assignment]
            session.flush()
            return product

    def set_active(self, product_id: int, *, active: bool) -> Product:
        with self.session() as session:
            product = session.get(Product, product_id)
            if product is None:
                raise InvalidProduct(f"No product with ID {product_id}")
            product.active = active
            session.flush()
            return product

    def history(self, product_id: int | None = None, *, limit: int = 100) -> list[PriceObservation]:
        with self.session() as session:
            query = select(PriceObservation).order_by(
                PriceObservation.checked_at.desc(), PriceObservation.id.desc()
            ).limit(limit)
            if product_id is not None:
                query = query.where(PriceObservation.product_id == product_id)
            return list(session.scalars(query))

    def alerts(self, product_id: int | None = None, *, limit: int = 100) -> list[AlertEvent]:
        with self.session() as session:
            query = select(AlertEvent).order_by(AlertEvent.id.desc()).limit(limit)
            if product_id is not None:
                query = query.where(AlertEvent.product_id == product_id)
            return list(session.scalars(query))

    def save_check(
        self, product_id: int, quote: PriceQuote
    ) -> tuple[PriceObservation, PriceObservation | None, list[AlertEvent]]:
        """Persist observation and its deduplicated alerts in ONE transaction."""
        with self.session() as session:
            product = session.get(Product, product_id)
            if product is None:
                raise InvalidProduct(f"No product with ID {product_id}")
            previous = session.scalar(
                select(PriceObservation)
                .where(PriceObservation.product_id == product_id)
                .order_by(PriceObservation.id.desc())
                .limit(1)
            )
            if previous and previous.currency != quote.currency:
                raise InvalidProduct("Currency changed; refusing to compare unlike values")
            observation = PriceObservation(
                product_id=product_id,
                name=quote.name.strip(),
                price=quote.price,
                currency=quote.currency,
                checked_at=quote.checked_at,
            )
            session.add(observation)
            product.name = quote.name.strip()
            product.currency = quote.currency
            session.flush()
            alerts: list[AlertEvent] = []
            if (
                product.target is not None
                and quote.price <= product.target
                and (previous is None or previous.price > product.target)
            ):
                alerts.append(
                        AlertEvent(
                            product_id=product.id,
                            observation_id=observation.id,
                            kind="target",
                            dedupe_key=f"{product.id}:target:{observation.id}",
                            message=f"Target reached: {quote.currency} {quote.price:.2f} "
                            f"<= {product.target:.2f}",
                        )
                )
            if (
                previous is not None
                and product.drop_percent is not None
                and previous.price > quote.price
                and ((previous.price - quote.price) / previous.price * 100)
                >= product.drop_percent
            ):
                drop = (previous.price - quote.price) / previous.price * 100
                alerts.append(
                    AlertEvent(
                        product_id=product.id,
                        observation_id=observation.id,
                        kind="drop",
                        dedupe_key=f"{product.id}:drop:{observation.id}",
                        message=f"Price dropped {drop:.2f}% to {quote.currency} {quote.price:.2f}",
                    )
                )
            session.add_all(alerts)
            session.flush()
            return observation, previous, alerts

    def close(self) -> None:
        self.engine.dispose()
