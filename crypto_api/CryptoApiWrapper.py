import config
from kryptoexpress import AsyncKryptoExpressClient, verify_callback_signature
from kryptoexpress.models import FiatCurrency as KryptoExpressFiatCurrency
from kryptoexpress.models import CryptoCurrency as KryptoExpressCryptoCurrency
from enums.cryptocurrency import Cryptocurrency
from enums.currency import Currency
from enums.payment import PaymentType
from enums.withdraw_type import WithdrawType
from models.payment import ProcessingPaymentDTO
from models.withdrawal import WithdrawalDTO

# UZS → USD konvertatsiya yordamchisi (yangi fayl: uzs_converter.py)
from utils.uzs_converter import uzs_to_usd, usd_to_uzs

# KryptoExpress UZS ni qabul qilmaydi, shuning uchun USD ishlatamiz
_UZS = Currency.UZS if hasattr(Currency, "UZS") else None
_SDK_USD = KryptoExpressFiatCurrency("USD")


class CryptoApiWrapper:
    @staticmethod
    def _map_crypto_to_sdk(cryptocurrency: Cryptocurrency) -> KryptoExpressCryptoCurrency:
        return KryptoExpressCryptoCurrency(cryptocurrency.value)

    @staticmethod
    def _map_crypto_from_sdk(cryptocurrency: KryptoExpressCryptoCurrency) -> Cryptocurrency:
        return Cryptocurrency(cryptocurrency.value)

    @staticmethod
    def _map_fiat_to_sdk(currency: Currency) -> KryptoExpressFiatCurrency:
        # UZS SDK da yo'q — USD bilan almashtiramiz
        if _UZS and currency == _UZS:
            return _SDK_USD
        return KryptoExpressFiatCurrency(currency.value)

    @staticmethod
    def _build_client() -> AsyncKryptoExpressClient:
        return AsyncKryptoExpressClient(
            api_key=config.KRYPTO_EXPRESS_API_KEY,
            base_url=config.KRYPTO_EXPRESS_API_URL,
        )

    @staticmethod
    def _build_processing_payment_dto(payment) -> ProcessingPaymentDTO:
        return ProcessingPaymentDTO(
            id=payment.id,
            paymentType=PaymentType(payment.payment_type.value),
            fiatCurrency=Currency(payment.fiat_currency.value),
            fiatAmount=payment.fiat_amount,
            cryptoAmount=payment.crypto_amount,
            cryptoCurrency=Cryptocurrency(payment.crypto_currency.value),
            expireDatetime=payment.expire_datetime,
            createDatetime=payment.create_datetime,
            address=payment.address,
            isPaid=payment.is_paid,
            isWithdrawn=payment.is_withdrawn,
            hash=payment.hash,
            callbackUrl=payment.callback_url,
        )

    @staticmethod
    def _build_withdrawal_dto(withdrawal) -> WithdrawalDTO:
        return WithdrawalDTO(
            withdrawType=WithdrawType(withdrawal.withdraw_type.value),
            cryptoCurrency=Cryptocurrency(withdrawal.crypto_currency.value),
            toAddress=withdrawal.to_address,
            txIdList=withdrawal.tx_id_list,
            receivingAmount=withdrawal.receiving_amount,
            blockchainFeeAmount=withdrawal.blockchain_fee_amount,
            serviceFeeAmount=withdrawal.service_fee_amount,
            onlyCalculate=withdrawal.only_calculate,
            totalWithdrawalAmount=withdrawal.total_withdrawal_amount,
            paymentId=withdrawal.payment_id,
        )

    @staticmethod
    async def create_invoice(payment_dto: ProcessingPaymentDTO, redis=None) -> ProcessingPaymentDTO:
        fiat_currency = payment_dto.fiatCurrency
        fiat_amount = payment_dto.fiatAmount

        # UZS bo'lsa — USD ga o'girib yuboramiz
        is_uzs = _UZS and fiat_currency == _UZS
        if is_uzs and fiat_amount is not None:
            fiat_amount = await uzs_to_usd(fiat_amount, redis)
            sdk_fiat = _SDK_USD
        else:
            sdk_fiat = CryptoApiWrapper._map_fiat_to_sdk(fiat_currency)

        async with CryptoApiWrapper._build_client() as client:
            if payment_dto.paymentType == PaymentType.PAYMENT:
                payment = await client.payments.create_payment(
                    crypto_currency=CryptoApiWrapper._map_crypto_to_sdk(payment_dto.cryptoCurrency),
                    fiat_currency=sdk_fiat,
                    fiat_amount=fiat_amount,
                    callback_url=payment_dto.callbackUrl,
                    callback_secret=payment_dto.callbackSecret,
                )
            else:
                payment = await client.payments.create_deposit(
                    crypto_currency=CryptoApiWrapper._map_crypto_to_sdk(payment_dto.cryptoCurrency),
                    fiat_currency=sdk_fiat,
                    callback_url=payment_dto.callbackUrl,
                    callback_secret=payment_dto.callbackSecret,
                )
        return CryptoApiWrapper._build_processing_payment_dto(payment)

    @staticmethod
    async def get_crypto_prices(redis=None) -> dict:
        # UZS bo'lsa — APIga USD so'raymiz, natijani UZS ga o'giramiz
        is_uzs = _UZS and config.CURRENCY == _UZS

        request_currency = _SDK_USD if is_uzs else CryptoApiWrapper._map_fiat_to_sdk(config.CURRENCY)

        async with CryptoApiWrapper._build_client() as client:
            prices_response = await client.currencies.get_prices(
                crypto_currencies=[
                    CryptoApiWrapper._map_crypto_to_sdk(cryptocurrency)
                    for cryptocurrency in Cryptocurrency
                ],
                fiat_currency=request_currency,
            )

        prices = {}
        # Fiat kalit har doim config.CURRENCY.value (masalan "uzs")
        fiat_key = config.CURRENCY.value.lower()

        for price in prices_response.prices:
            internal_currency = CryptoApiWrapper._map_crypto_from_sdk(price.crypto_currency)
            raw_price = price.price

            # USD da kelgan narxni UZS ga o'giramiz
            if is_uzs:
                raw_price = await usd_to_uzs(raw_price, redis)

            prices[internal_currency.get_coingecko_name()] = {fiat_key: raw_price}

        return prices

    @staticmethod
    async def get_wallet_balance() -> dict[Cryptocurrency, float]:
        async with CryptoApiWrapper._build_client() as client:
            wallet = await client.wallet.get()
        balances: dict[Cryptocurrency, float] = {}
        for currency_name, amount in wallet.model_dump(exclude_none=True).items():
            try:
                balances[Cryptocurrency(currency_name)] = amount
            except ValueError:
                continue
        return balances

    @staticmethod
    async def withdrawal(cryptocurrency: Cryptocurrency,
                         to_address: str,
                         only_calculate: bool,
                         payment_id: int = None) -> WithdrawalDTO:
        sdk_currency = CryptoApiWrapper._map_crypto_to_sdk(cryptocurrency)
        async with CryptoApiWrapper._build_client() as client:
            if payment_id:
                if only_calculate:
                    withdrawal = await client.wallet.calculate_single(
                        payment_id=payment_id,
                        crypto_currency=sdk_currency,
                        to_address=to_address,
                    )
                else:
                    withdrawal = await client.wallet.withdraw_single(
                        payment_id=payment_id,
                        crypto_currency=sdk_currency,
                        to_address=to_address,
                    )
            else:
                if only_calculate:
                    withdrawal = await client.wallet.calculate_all(
                        crypto_currency=sdk_currency,
                        to_address=to_address,
                    )
                else:
                    withdrawal = await client.wallet.withdraw_all(
                        crypto_currency=sdk_currency,
                        to_address=to_address,
                    )
        return CryptoApiWrapper._build_withdrawal_dto(withdrawal)

    @staticmethod
    def verify_callback_signature(signature: str | None, payload: bytes) -> bool:
        if not config.KRYPTO_EXPRESS_API_SECRET:
            return False
        return verify_callback_signature(
            raw_body=payload,
            callback_secret=config.KRYPTO_EXPRESS_API_SECRET,
            signature=signature,
        )
